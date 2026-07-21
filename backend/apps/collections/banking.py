"""
Bank reconciliation + cheque-bounce handling (CLAUDE.md roadmap).

Reconciliation matches imported bank-statement credit lines to recorded
Payments (by amount + reference/date). Cheque-bounce voids a dishonoured cheque
payment, reverses the credit it gave the invoice, and optionally levies a bounce
charge. All money is Decimal; every action is audited.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .models import (
    BankStatement,
    BankStatementLine,
    ChequeBounce,
    Invoice,
    InvoiceStatus,
    Payment,
)
from .services import _quantize, _sync_status, apply_late_fee, sync_plan_allocation

log = get_logger("collections.banking")

_MATCH_DATE_WINDOW = 3  # days either side when matching by date


@transaction.atomic
def import_bank_statement(*, label: str, account_ref: str, rows, actor=None) -> BankStatement:
    """`rows`: [{txn_date, description?, reference?, amount}] (amount +credit/−debit)."""
    statement = BankStatement.objects.create(
        label=label,
        account_ref=account_ref,
        imported_by=actor if getattr(actor, "pk", None) else None,
    )
    created = 0
    for r in rows:
        BankStatementLine.objects.create(
            statement=statement,
            txn_date=r["txn_date"],
            description=r.get("description", ""),
            reference=r.get("reference", ""),
            amount=_quantize(Decimal(r["amount"])),
        )
        created += 1
    log.info(
        "bank statement imported label=%s lines=%s",
        label,
        created,
        **ctx(user=getattr(actor, "id", "-"), entity=statement.id, action="import_bank_statement"),
    )
    record_audit(
        action="bank_statement.imported",
        entity=statement,
        summary=f"Imported {created} lines from {label}",
        actor=actor,
    )
    return statement


def _find_payment_for(line: BankStatementLine) -> Payment | None:
    """A recorded, not-yet-reconciled payment matching this credit line."""
    candidates = Payment.objects.filter(
        amount=line.amount,
        status=Payment.Status.RECORDED,
        bank_lines__isnull=True,
    )
    # Prefer an exact reference (UTR / cheque no) match.
    if line.reference:
        exact = candidates.filter(reference=line.reference).first()
        if exact:
            return exact
    # Else match on date proximity.
    lo = line.txn_date - timedelta(days=_MATCH_DATE_WINDOW)
    hi = line.txn_date + timedelta(days=_MATCH_DATE_WINDOW)
    return (
        candidates.filter(paid_at__date__gte=lo, paid_at__date__lte=hi).order_by("paid_at").first()
    )


@transaction.atomic
def auto_reconcile(*, statement: BankStatement | None = None, actor=None) -> dict:
    """
    Match unmatched CREDIT lines to payments. Returns {matched, unmatched}.
    Debit lines are left alone (they aren't fee income).
    """
    lines = BankStatementLine.objects.filter(
        status=BankStatementLine.Status.UNMATCHED, amount__gt=ZERO
    )
    if statement is not None:
        lines = lines.filter(statement=statement)

    matched = 0
    for line in lines.select_for_update():
        payment = _find_payment_for(line)
        if payment is None:
            continue
        line.payment = payment
        line.status = BankStatementLine.Status.MATCHED
        line.save(update_fields=["payment", "status", "updated_at"])
        matched += 1

    remaining = BankStatementLine.objects.filter(
        status=BankStatementLine.Status.UNMATCHED, amount__gt=ZERO
    )
    if statement is not None:
        remaining = remaining.filter(statement=statement)
    unmatched = remaining.count()

    log.info(
        "bank reconcile matched=%s unmatched=%s",
        matched,
        unmatched,
        **ctx(user=getattr(actor, "id", "-"), action="auto_reconcile"),
    )
    if matched:
        record_audit(
            action="bank.reconciled",
            entity=statement,
            summary=f"Reconciled {matched} bank line(s); {unmatched} unmatched",
            actor=actor,
        )
    return {"matched": matched, "unmatched": unmatched}


@transaction.atomic
def bounce_cheque(*, payment: Payment, reason: str = "", charge=None, actor=None) -> ChequeBounce:
    """
    Dishonour a cheque payment: void it, reverse the credit it gave the invoice,
    and levy an optional bounce charge (added as a late fee). Not idempotent by
    key — guards against re-bouncing an already-void payment.
    """
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status == Payment.Status.VOID:
        raise ServiceError("Payment is already void.")

    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
    charge = _quantize(Decimal(charge if charge is not None else settings.CHEQUE_BOUNCE_CHARGE))

    # Reverse the credit this payment gave.
    invoice.amount_paid = _quantize(invoice.amount_paid - payment.amount)
    if invoice.amount_paid < ZERO:
        invoice.amount_paid = ZERO
    payment.status = Payment.Status.VOID
    payment.save(update_fields=["status", "updated_at"])

    if invoice.status != InvoiceStatus.CANCELLED:
        _sync_status(invoice)
    invoice.save(update_fields=["amount_paid", "status", "updated_at"])

    bounce = ChequeBounce.objects.create(
        payment=payment,
        invoice=invoice,
        reason=reason,
        charge=charge,
        recorded_by=actor if getattr(actor, "pk", None) else None,
    )
    if charge > ZERO:
        apply_late_fee(invoice, charge, actor=actor)
    invoice.refresh_from_db()
    sync_plan_allocation(invoice)

    log.warning(
        "cheque bounced payment=%s invoice=%s reversed=%s charge=%s",
        payment.id,
        invoice.invoice_number,
        payment.amount,
        charge,
        **ctx(user=getattr(actor, "id", "-"), entity=payment.id, action="bounce_cheque"),
    )
    record_audit(
        action="cheque.bounced",
        entity=payment,
        summary=(
            f"Cheque bounced on {invoice.invoice_number}: reversed {payment.amount} "
            f"{invoice.currency}" + (f", charge {charge}" if charge > ZERO else "")
        ),
        actor=actor,
    )
    return bounce
