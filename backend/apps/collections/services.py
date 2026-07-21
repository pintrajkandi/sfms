"""
Invoice & payment business logic (CLAUDE.md §5).

All money math is Decimal. Status changes go through guarded transitions.
Payment recording is idempotent via a client-supplied idempotency key.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .models import (
    AppliedDiscount,
    CreditNote,
    Installment,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    Payment,
    PaymentPlan,
    Refund,
)

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
    """
    Subtotal from lines; total = subtotal − discount − adjustment + late fee.
    Never trust the client. `adjustment_amount` carries post-issue credit notes.
    """
    subtotal = sum((line.amount for line in invoice.lines.all()), ZERO)
    invoice.subtotal = _quantize(Decimal(subtotal))
    invoice.total = _quantize(
        invoice.subtotal
        - invoice.discount_amount
        - invoice.adjustment_amount
        + invoice.late_fee_amount
    )
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
    discount_amount: Decimal | None = None,
    late_fee_amount: Decimal = ZERO,
    currency: str = "USD",
    apply_discount_rules: bool = True,
    actor=None,
) -> Invoice:
    """
    `lines`: [{fee_type, quantity, unit_price, description?}].

    Discounts: pass an explicit `discount_amount` to override, or leave it None
    and let `apply_discount_rules` resolve the student's scholarships/concessions/
    sibling rules (fees.services.resolve_discounts) — each contributing rule is
    recorded as an AppliedDiscount for audit.
    """
    invoice = Invoice.objects.create(
        invoice_number=next_invoice_number(),
        student=student,
        academic_year=academic_year,
        due_date=due_date,
        discount_amount=ZERO,
        late_fee_amount=_quantize(Decimal(late_fee_amount)),
        currency=currency,
        status=InvoiceStatus.DRAFT,
    )
    by_fee_type: dict[int, Decimal] = {}
    for line in lines:
        qty = int(line.get("quantity", 1))
        unit = _quantize(Decimal(line["unit_price"]))
        amount = _quantize(unit * qty)
        fee_type = line["fee_type"]
        InvoiceLine.objects.create(
            invoice=invoice,
            fee_type=fee_type,
            description=line.get("description", ""),
            quantity=qty,
            unit_price=unit,
            amount=amount,
        )
        by_fee_type[fee_type.id] = by_fee_type.get(fee_type.id, ZERO) + amount

    subtotal = _quantize(Decimal(sum(by_fee_type.values(), ZERO)))

    if discount_amount is not None:
        invoice.discount_amount = _quantize(Decimal(discount_amount))
    elif apply_discount_rules:
        from apps.fees.services import resolve_discounts

        total_discount, applied = resolve_discounts(
            student, subtotal=subtotal, by_fee_type=by_fee_type
        )
        invoice.discount_amount = total_discount
        for a in applied:
            AppliedDiscount.objects.create(
                invoice=invoice,
                rule_id=a.rule_id,
                code=a.code,
                name=a.name,
                kind=a.kind,
                amount=a.amount,
            )

    recompute_totals(invoice)
    _sync_status(invoice)
    invoice.save()
    log.info(
        "invoice generated number=%s total=%s discount=%s",
        invoice.invoice_number,
        invoice.total,
        invoice.discount_amount,
        **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="generate_invoice"),
    )
    record_audit(
        action="invoice.created",
        entity=invoice,
        summary=(
            f"Invoice {invoice.invoice_number} for {student.full_name} "
            f"— {invoice.total} {invoice.currency}"
        ),
        actor=actor,
    )
    from apps.finance.ledger import _safe, post_invoice_issued

    _safe(post_invoice_issued, invoice)
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

    # Re-derive the instalment schedule from the new amount_paid (idempotent).
    sync_plan_allocation(invoice)

    log.info(
        "payment recorded amount=%s method=%s invoice=%s status=%s",
        amount,
        method,
        invoice.invoice_number,
        invoice.status,
        **ctx(user=getattr(actor, "id", "-"), entity=payment.id, action="record_payment"),
    )
    record_audit(
        action="payment.recorded",
        entity=payment,
        summary=(
            f"Payment {amount} {invoice.currency} via {method} on "
            f"{invoice.invoice_number} (now {invoice.status})"
        ),
        actor=actor,
    )

    # Digitally sign the receipt — best-effort, never breaks the payment write.
    try:
        from .signatures import sign_receipt

        sign_receipt(payment, actor=actor)
    except Exception as exc:
        log.warning(
            "receipt signing skipped payment=%s error=%s",
            payment.id,
            exc,
            **ctx(user=getattr(actor, "id", "-"), entity=payment.id, action="sign_receipt"),
        )

    from apps.finance.ledger import _safe, post_payment

    _safe(post_payment, payment)
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


# --------------------------------------------------------------------------- #
# Instalments / payment plans.
# --------------------------------------------------------------------------- #
def _split_amount(total: Decimal, count: int) -> list[Decimal]:
    """Even split of `total` into `count` cents-exact parts; remainder on the last."""
    each = _quantize(total / count)
    parts = [each] * (count - 1)
    parts.append(_quantize(total - each * (count - 1)))
    return parts


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    # Clamp day to the target month's length (28 is always safe for schedules).
    day = min(d.day, 28)
    return date(year, month, day)


@transaction.atomic
def create_payment_plan(
    *,
    invoice: Invoice,
    count: int | None = None,
    first_due_date: date | None = None,
    frequency: str = "monthly",
    schedule: Iterable[dict] | None = None,
    actor=None,
) -> PaymentPlan:
    """
    Build an instalment schedule for an invoice's total.

    Either pass `schedule` = [{due_date, amount}] (amounts must sum to the total),
    or `count` + `first_due_date` for an even split (monthly/weekly). Fails if a
    plan already exists or the invoice has nothing/negative to bill.
    """
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ServiceError("Cannot plan a cancelled invoice.")
    if invoice.total <= ZERO:
        raise ServiceError("Invoice has no amount to schedule.")
    if PaymentPlan.objects.filter(invoice=invoice).exists():
        raise ServiceError("Invoice already has a payment plan.")

    rows: list[dict] = []
    if schedule is not None:
        rows = [
            {"due_date": s["due_date"], "amount": _quantize(Decimal(s["amount"]))} for s in schedule
        ]
        if len(rows) < 2:
            raise ServiceError("A payment plan needs at least two instalments.")
        if sum((r["amount"] for r in rows), ZERO) != invoice.total:
            raise ServiceError("Instalment amounts must sum to the invoice total.")
    else:
        if not count or count < 2:
            raise ServiceError("A payment plan needs at least two instalments.")
        start = first_due_date or invoice.due_date or timezone.now().date()
        step = 7 if frequency == "weekly" else None
        amounts = _split_amount(invoice.total, count)
        for i, amt in enumerate(amounts):
            due = start + timedelta(days=step * i) if step else _add_months(start, i)
            rows.append({"due_date": due, "amount": amt})

    plan = PaymentPlan.objects.create(
        invoice=invoice,
        created_by=actor if getattr(actor, "pk", None) else None,
    )
    for i, r in enumerate(rows, start=1):
        Installment.objects.create(
            plan=plan, sequence=i, due_date=r["due_date"], amount=r["amount"]
        )
    sync_plan_allocation(invoice)
    log.info(
        "payment plan created invoice=%s instalments=%s total=%s",
        invoice.invoice_number,
        len(rows),
        invoice.total,
        **ctx(user=getattr(actor, "id", "-"), entity=plan.id, action="create_payment_plan"),
    )
    return plan


def sync_plan_allocation(invoice: Invoice) -> None:
    """
    Waterfall the invoice's amount_paid across its instalments oldest-first and
    set each instalment's status. Idempotent — derived purely from amount_paid, so
    it can run after every payment/refund without double-counting.
    """
    plan = PaymentPlan.objects.filter(invoice=invoice).first()
    if plan is None:
        return

    remaining = invoice.amount_paid
    today = date.today()
    for inst in plan.installments.order_by("sequence"):
        applied = min(inst.amount, remaining) if remaining > ZERO else ZERO
        applied = _quantize(applied)
        remaining = _quantize(remaining - applied)
        inst.amount_paid = applied
        if applied >= inst.amount and inst.amount > ZERO:
            inst.status = Installment.Status.PAID
        elif applied > ZERO:
            inst.status = Installment.Status.PARTIAL
        elif inst.due_date < today:
            inst.status = Installment.Status.OVERDUE
        else:
            inst.status = Installment.Status.PENDING
        inst.save(update_fields=["amount_paid", "status", "updated_at"])

    all_paid = all(i.status == Installment.Status.PAID for i in plan.installments.all())
    new_status = PaymentPlan.Status.COMPLETED if all_paid else PaymentPlan.Status.ACTIVE
    if plan.status != PaymentPlan.Status.CANCELLED and plan.status != new_status:
        plan.status = new_status
        plan.save(update_fields=["status", "updated_at"])


# --------------------------------------------------------------------------- #
# Refunds (cash out) & credit notes (reduce what's owed, no cash).
# --------------------------------------------------------------------------- #
@transaction.atomic
def record_refund(
    *,
    invoice: Invoice,
    amount: Decimal,
    method: str,
    idempotency_key: str,
    reason: str = "",
    payment: Payment | None = None,
    actor=None,
) -> Refund:
    """
    Return cash to the payer. Idempotent via idempotency_key. Reduces the
    invoice's amount_paid (can't refund more than was paid) and re-syncs status.
    """
    amount = _quantize(Decimal(amount))
    if amount <= ZERO:
        raise ServiceError("Refund amount must be positive.")

    existing = Refund.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        log.warning(
            "duplicate refund ignored key=%s",
            idempotency_key,
            **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="record_refund"),
        )
        return existing

    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if amount > invoice.amount_paid:
        raise ServiceError("Refund exceeds the amount paid.")

    try:
        refund = Refund.objects.create(
            invoice=invoice,
            payment=payment,
            amount=amount,
            currency=invoice.currency,
            method=method,
            reason=reason,
            idempotency_key=idempotency_key,
            processed_by=actor if getattr(actor, "pk", None) else None,
        )
    except IntegrityError:
        return Refund.objects.get(idempotency_key=idempotency_key)

    invoice.amount_paid = _quantize(invoice.amount_paid - amount)
    _sync_status(invoice)
    invoice.save(update_fields=["amount_paid", "status", "updated_at"])
    sync_plan_allocation(invoice)

    log.info(
        "refund processed amount=%s method=%s invoice=%s status=%s",
        amount,
        method,
        invoice.invoice_number,
        invoice.status,
        **ctx(user=getattr(actor, "id", "-"), entity=refund.id, action="record_refund"),
    )
    record_audit(
        action="refund.processed",
        entity=refund,
        summary=f"Refund {amount} {invoice.currency} on {invoice.invoice_number}",
        actor=actor,
    )
    from apps.finance.ledger import _safe, post_refund

    _safe(post_refund, refund)
    return refund


def next_credit_note_number(prefix: str = "CN") -> str:
    year = timezone.now().year
    stem = f"{prefix}-{year}-"
    last = (
        CreditNote.objects.filter(credit_note_number__startswith=stem)
        .order_by("-credit_note_number")
        .values_list("credit_note_number", flat=True)
        .first()
    )
    seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{stem}{seq:05d}"


@transaction.atomic
def issue_credit_note(
    *,
    invoice: Invoice,
    amount: Decimal,
    kind: str = CreditNote.Kind.ADJUSTMENT,
    reason: str = "",
    actor=None,
) -> CreditNote:
    """
    Credit the student's bill (no cash movement): corrections, write-offs,
    goodwill concessions. Accrues into adjustment_amount, cutting the total — but
    never below what's already been paid.
    """
    amount = _quantize(Decimal(amount))
    if amount <= ZERO:
        raise ServiceError("Credit note amount must be positive.")

    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ServiceError("Cannot credit a cancelled invoice.")
    if amount > invoice.balance:
        raise ServiceError("Credit note exceeds the outstanding balance.")

    note = CreditNote.objects.create(
        invoice=invoice,
        credit_note_number=next_credit_note_number(),
        amount=amount,
        currency=invoice.currency,
        kind=kind,
        reason=reason,
        issued_by=actor if getattr(actor, "pk", None) else None,
    )
    invoice.adjustment_amount = _quantize(invoice.adjustment_amount + amount)
    recompute_totals(invoice)
    _sync_status(invoice)
    invoice.save()
    sync_plan_allocation(invoice)

    log.info(
        "credit note issued number=%s amount=%s invoice=%s total=%s",
        note.credit_note_number,
        amount,
        invoice.invoice_number,
        invoice.total,
        **ctx(user=getattr(actor, "id", "-"), entity=note.id, action="issue_credit_note"),
    )
    record_audit(
        action="credit_note.issued",
        entity=note,
        summary=(
            f"Credit note {note.credit_note_number} ({kind}) {amount} "
            f"{invoice.currency} on {invoice.invoice_number}"
        ),
        actor=actor,
    )
    return note
