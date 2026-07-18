"""
Invoice & payment business logic (CLAUDE.md §5).

All money math is Decimal. Status changes go through guarded transitions.
Payment recording is idempotent via a client-supplied idempotency key.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .models import Invoice, InvoiceLine, InvoiceStatus, Payment

log = get_logger("collections")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def next_invoice_number(prefix: str = "INV") -> str:
    year = timezone.now().year
    stem = f"{prefix}-{year}-"
    last = (
        Invoice.objects.filter(invoice_number__startswith=stem)
        .order_by("-invoice_number")
        .values_list("invoice_number", flat=True)
        .first()
    )
    seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{stem}{seq:05d}"


def recompute_totals(invoice: Invoice) -> Invoice:
    """Subtotal from lines; total = subtotal − discount + late fee. Never trust the client."""
    subtotal = sum((line.amount for line in invoice.lines.all()), ZERO)
    invoice.subtotal = _quantize(Decimal(subtotal))
    invoice.total = _quantize(invoice.subtotal - invoice.discount_amount + invoice.late_fee_amount)
    return invoice


def _sync_status(invoice: Invoice) -> None:
    """Derive pending/partial/paid/overdue from money + due date. Guarded — no cancels here."""
    if invoice.status == InvoiceStatus.CANCELLED:
        return
    if invoice.amount_paid >= invoice.total and invoice.total > ZERO:
        invoice.status = InvoiceStatus.PAID
    elif invoice.amount_paid > ZERO:
        invoice.status = InvoiceStatus.PARTIAL
    elif invoice.due_date and invoice.due_date < date.today():
        invoice.status = InvoiceStatus.OVERDUE
    else:
        invoice.status = InvoiceStatus.PENDING


@transaction.atomic
def create_invoice(
    *,
    student,
    lines: Iterable[dict],
    academic_year=None,
    due_date: date | None = None,
    discount_amount: Decimal = ZERO,
    late_fee_amount: Decimal = ZERO,
    currency: str = "USD",
    actor=None,
) -> Invoice:
    """`lines`: [{fee_type, quantity, unit_price, description?}]."""
    invoice = Invoice.objects.create(
        invoice_number=next_invoice_number(),
        student=student,
        academic_year=academic_year,
        due_date=due_date,
        discount_amount=_quantize(Decimal(discount_amount)),
        late_fee_amount=_quantize(Decimal(late_fee_amount)),
        currency=currency,
        status=InvoiceStatus.DRAFT,
    )
    for line in lines:
        qty = int(line.get("quantity", 1))
        unit = _quantize(Decimal(line["unit_price"]))
        InvoiceLine.objects.create(
            invoice=invoice,
            fee_type=line["fee_type"],
            description=line.get("description", ""),
            quantity=qty,
            unit_price=unit,
            amount=_quantize(unit * qty),
        )
    recompute_totals(invoice)
    _sync_status(invoice)
    invoice.save()
    log.info(
        "invoice generated number=%s total=%s",
        invoice.invoice_number,
        invoice.total,
        **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="generate_invoice"),
    )
    return invoice


@transaction.atomic
def record_payment(
    *,
    invoice: Invoice,
    amount: Decimal,
    method: str,
    idempotency_key: str,
    paid_at=None,
    reference: str = "",
    actor=None,
) -> Payment:
    """
    Idempotent: a repeat with the same idempotency_key returns the existing payment
    without double-crediting the invoice.
    """
    amount = _quantize(Decimal(amount))
    if amount <= ZERO:
        raise ServiceError("Payment amount must be positive.")

    existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        log.warning(
            "duplicate payment ignored key=%s",
            idempotency_key,
            **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="record_payment"),
        )
        return existing

    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ServiceError("Cannot record a payment against a cancelled invoice.")
    if amount > invoice.balance:
        raise ServiceError("Payment exceeds the outstanding balance.")

    try:
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            currency=invoice.currency,
            method=method,
            reference=reference,
            paid_at=paid_at or timezone.now(),
            idempotency_key=idempotency_key,
            recorded_by=actor if getattr(actor, "pk", None) else None,
        )
    except IntegrityError:
        # Lost the race to a concurrent identical submit — return the winner.
        return Payment.objects.get(idempotency_key=idempotency_key)

    invoice.amount_paid = _quantize(invoice.amount_paid + amount)
    _sync_status(invoice)
    invoice.save(update_fields=["amount_paid", "status", "updated_at"])

    log.info(
        "payment recorded amount=%s method=%s invoice=%s status=%s",
        amount,
        method,
        invoice.invoice_number,
        invoice.status,
        **ctx(user=getattr(actor, "id", "-"), entity=payment.id, action="record_payment"),
    )
    return payment


@transaction.atomic
def apply_late_fee(invoice: Invoice, amount: Decimal, *, actor=None) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    invoice.late_fee_amount = _quantize(invoice.late_fee_amount + Decimal(amount))
    recompute_totals(invoice)
    _sync_status(invoice)
    invoice.save()
    log.warning(
        "late fee applied amount=%s invoice=%s",
        amount,
        invoice.invoice_number,
        **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="apply_late_fee"),
    )
    return invoice
