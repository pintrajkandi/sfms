"""
UPI Autopay / e-mandates (CLAUDE.md roadmap).

A mandate authorises recurring auto-debit of a student's fees up to a per-debit
ceiling. Razorpay holds the real mandate/subscription; we store its token +
lifecycle and attempt debits via dispatch_autopay. Like the rest of the gateway
layer this is env-gated: with no Razorpay creds we mock the token + debit so the
whole flow is exercisable in dev. Debits post through the idempotent
record_payment, so a mandate can never double-credit an invoice.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from django.db import transaction

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .gateway import razorpay_enabled
from .models import Invoice, InvoiceStatus, Mandate, MandateCharge
from .services import _quantize, record_payment

log = get_logger("collections.mandates")


def _add_period(d: date, frequency: str) -> date:
    months = {"monthly": 1, "quarterly": 3}.get(frequency, 1)
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    return date(year, month, min(d.day, 28))


def _gateway_create_mandate(mandate: Mandate) -> dict:  # pragma: no cover - network path
    """Create the real Razorpay subscription/token. Stubbed thin."""
    import razorpay  # noqa: F401 - real integration wired here

    raise ServiceError("Razorpay e-mandate creation not wired in this build.")


def _mock_mandate(mandate: Mandate) -> dict:
    ref = f"mock_mandate_{uuid.uuid4().hex[:16]}"
    return {
        "gateway_ref": ref,
        "gateway_customer": f"mock_cust_{uuid.uuid4().hex[:10]}",
        "auth_url": f"https://example.test/authorize/{ref}",
    }


@transaction.atomic
def create_mandate(
    *,
    student,
    max_amount,
    frequency: str = Mandate.Frequency.AS_PRESENTED,
    currency: str = "INR",
    payer_vpa: str = "",
    start_on: date | None = None,
    actor=None,
) -> Mandate:
    """Register an e-mandate (status CREATED, awaiting payer authorisation)."""
    max_amount = _quantize(Decimal(max_amount))
    if max_amount <= ZERO:
        raise ServiceError("Mandate max amount must be positive.")

    mandate = Mandate(
        student=student,
        max_amount=max_amount,
        frequency=frequency,
        currency=currency,
        payer_vpa=payer_vpa,
        start_on=start_on,
        created_by=actor if getattr(actor, "pk", None) else None,
    )
    result = _gateway_create_mandate(mandate) if razorpay_enabled() else _mock_mandate(mandate)
    mandate.gateway_ref = result["gateway_ref"]
    mandate.gateway_customer = result.get("gateway_customer", "")
    mandate.auth_url = result.get("auth_url", "")
    mandate.save()

    log.info(
        "mandate created student=%s ref=%s max=%s live=%s",
        student.pk,
        mandate.gateway_ref,
        max_amount,
        razorpay_enabled(),
        **ctx(user=getattr(actor, "id", "-"), entity=mandate.id, action="create_mandate"),
    )
    record_audit(
        action="mandate.created",
        entity=mandate,
        summary=f"E-mandate for {student.full_name} up to {max_amount} {currency}",
        actor=actor,
    )
    return mandate


@transaction.atomic
def activate_mandate(mandate: Mandate, *, actor=None) -> Mandate:
    """Mark a mandate authorised & active (called on payer approval / webhook)."""
    mandate = Mandate.objects.select_for_update().get(pk=mandate.pk)
    if mandate.status == Mandate.Status.CANCELLED:
        raise ServiceError("Cannot activate a cancelled mandate.")
    mandate.status = Mandate.Status.ACTIVE
    if mandate.next_charge_on is None:
        mandate.next_charge_on = mandate.start_on or date.today()
    mandate.save(update_fields=["status", "next_charge_on", "updated_at"])
    log.info(
        "mandate activated ref=%s",
        mandate.gateway_ref,
        **ctx(user=getattr(actor, "id", "-"), entity=mandate.id, action="activate_mandate"),
    )
    record_audit(
        action="mandate.activated", entity=mandate, summary="E-mandate activated", actor=actor
    )
    return mandate


@transaction.atomic
def cancel_mandate(mandate: Mandate, *, actor=None) -> Mandate:
    mandate = Mandate.objects.select_for_update().get(pk=mandate.pk)
    mandate.status = Mandate.Status.CANCELLED
    mandate.save(update_fields=["status", "updated_at"])
    log.info(
        "mandate cancelled ref=%s",
        mandate.gateway_ref,
        **ctx(user=getattr(actor, "id", "-"), entity=mandate.id, action="cancel_mandate"),
    )
    record_audit(
        action="mandate.cancelled", entity=mandate, summary="E-mandate cancelled", actor=actor
    )
    return mandate


def _gateway_debit(mandate: Mandate, amount: Decimal) -> str:  # pragma: no cover - network path
    """Trigger the real Razorpay recurring charge; return the gateway payment id."""
    raise ServiceError("Razorpay recurring debit not wired in this build.")


@transaction.atomic
def charge_mandate(*, mandate: Mandate, invoice: Invoice, amount=None, actor=None) -> MandateCharge:
    """
    Auto-debit `amount` (default the invoice balance) against an active mandate,
    then post it through record_payment. Idempotent per (mandate, invoice, month).
    """
    mandate = Mandate.objects.select_for_update().get(pk=mandate.pk)
    if mandate.status != Mandate.Status.ACTIVE:
        raise ServiceError("Mandate is not active.")
    if invoice.student_id != mandate.student_id:
        raise ServiceError("Invoice does not belong to the mandate's student.")
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ServiceError("Cannot charge a cancelled invoice.")

    amount = _quantize(Decimal(amount) if amount is not None else invoice.balance)
    if amount <= ZERO:
        raise ServiceError("Nothing to charge.")
    if amount > mandate.max_amount:
        raise ServiceError("Charge exceeds the mandate's authorised amount.")
    if amount > invoice.balance:
        amount = invoice.balance

    period = date.today().strftime("%Y-%m")
    key = f"mandate:{mandate.id}:inv:{invoice.id}:{period}"
    existing = MandateCharge.objects.filter(idempotency_key=key).first()
    if existing and existing.status == MandateCharge.Status.SUCCEEDED:
        return existing

    charge = existing or MandateCharge(
        mandate=mandate,
        invoice=invoice,
        amount=amount,
        currency=mandate.currency,
        idempotency_key=key,
    )
    try:
        gateway_payment_id = (
            _gateway_debit(mandate, amount)
            if razorpay_enabled()
            else f"mock_pay_{uuid.uuid4().hex[:18]}"
        )
        payment = record_payment(
            invoice=invoice,
            amount=amount,
            method="upi",
            idempotency_key=gateway_payment_id,
            reference=gateway_payment_id,
            actor=actor,
        )
    except ServiceError as exc:
        charge.status = MandateCharge.Status.FAILED
        charge.error = str(exc)[:255]
        charge.save()
        log.warning(
            "mandate charge failed mandate=%s invoice=%s reason=%s",
            mandate.id,
            invoice.invoice_number,
            exc,
            **ctx(user=getattr(actor, "id", "-"), entity=mandate.id, action="charge_mandate"),
        )
        return charge

    charge.status = MandateCharge.Status.SUCCEEDED
    charge.gateway_payment_id = gateway_payment_id
    charge.payment = payment
    charge.error = ""
    charge.save()

    mandate.next_charge_on = _add_period(date.today(), mandate.frequency)
    mandate.save(update_fields=["next_charge_on", "updated_at"])

    log.info(
        "mandate charged mandate=%s invoice=%s amount=%s",
        mandate.id,
        invoice.invoice_number,
        amount,
        **ctx(user=getattr(actor, "id", "-"), entity=charge.id, action="charge_mandate"),
    )
    record_audit(
        action="mandate.charged",
        entity=charge,
        summary=f"Auto-debit {amount} {mandate.currency} on {invoice.invoice_number}",
        actor=actor,
    )
    return charge
