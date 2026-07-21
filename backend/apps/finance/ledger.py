"""
Double-entry accounting engine (CLAUDE.md §5 — money in services).

`post_journal` writes a balanced JournalEntry (debits == credits). Per-event
helpers turn business documents into journal entries so the General Ledger,
Trial Balance, P&L and Balance Sheet stay correct. Postings are idempotent per
(source_type, source_id), so replays never double-count.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import transaction

from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .models import Account, AccountType, JournalEntry, JournalLine

log = get_logger("finance.ledger")


def _q(v) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"))


# --------------------------------------------------------------------------- #
# Chart of accounts — default heads seeded per school (admin can add more).
# --------------------------------------------------------------------------- #
DEFAULT_ACCOUNTS = [
    ("1000", "Cash", AccountType.ASSET),
    ("1010", "Bank", AccountType.ASSET),
    ("1100", "Fees Receivable", AccountType.ASSET),
    ("1200", "Inventory", AccountType.ASSET),
    ("2000", "Fees Received in Advance", AccountType.LIABILITY),
    ("2100", "Salaries Payable", AccountType.LIABILITY),
    ("2200", "Statutory Dues Payable", AccountType.LIABILITY),
    ("2300", "Accounts Payable", AccountType.LIABILITY),
    ("3000", "Owner's Equity", AccountType.EQUITY),
    ("4000", "Fee Income", AccountType.INCOME),
    ("4100", "Other Income", AccountType.INCOME),
    ("5000", "Salaries & Wages", AccountType.EXPENSE),
    ("5100", "Operating Expenses", AccountType.EXPENSE),
    ("5200", "Refunds & Concessions", AccountType.EXPENSE),
    ("5300", "Transport Expenses", AccountType.EXPENSE),
]


def seed_chart_of_accounts() -> int:
    """Idempotently seed the default chart of accounts. Returns count created."""
    created = 0
    for code, name, acc_type in DEFAULT_ACCOUNTS:
        _, was_created = Account.objects.get_or_create(
            code=code, defaults={"name": name, "type": acc_type, "is_system": True}
        )
        created += int(was_created)
    log.info("chart of accounts seeded created=%s", created, **ctx(action="seed_coa"))
    return created


def _cash_account(method: str) -> str:
    return "1000" if (method or "").lower() == "cash" else "1010"


@transaction.atomic
def post_journal(*, date, lines, narration="", source_type="", source_id=None) -> JournalEntry:
    """
    Write a balanced journal entry. `lines` is a list of dicts:
    {"account": <code or Account>, "debit": D, "credit": D, "description"?: str}.
    """
    if source_type and source_id is not None:
        existing = JournalEntry.objects.filter(source_type=source_type, source_id=source_id).first()
        if existing:
            return existing

    total_debit = sum((_q(row.get("debit", 0)) for row in lines), ZERO)
    total_credit = sum((_q(row.get("credit", 0)) for row in lines), ZERO)
    if total_debit != total_credit:
        raise ServiceError(f"Unbalanced journal: debit {total_debit} != credit {total_credit}.")
    if total_debit <= ZERO:
        raise ServiceError("Journal entry has no amounts.")

    codes = {r["account"] for r in lines if isinstance(r["account"], str)}
    accounts = {a.code: a for a in Account.objects.filter(code__in=codes)}

    entry = JournalEntry.objects.create(
        date=date, narration=narration, source_type=source_type, source_id=source_id
    )
    for row in lines:
        acc = row["account"]
        if isinstance(acc, str):
            acc = accounts.get(acc)
            if acc is None:
                raise ServiceError(f"Unknown account code {row['account']}.")
        JournalLine.objects.create(
            entry=entry,
            account=acc,
            debit=_q(row.get("debit", 0)),
            credit=_q(row.get("credit", 0)),
            description=row.get("description", ""),
        )
    return entry


def _safe(fn, *args):
    """Posting must never break the underlying business operation."""
    try:
        fn(*args)
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("journal posting skipped: %s", exc, **ctx(action="post_journal"))


# --------------------------------------------------------------------------- #
# Per-event postings (called best-effort from the relevant services).
# --------------------------------------------------------------------------- #
def post_invoice_issued(invoice) -> None:
    total = _q(invoice.total)
    if total <= ZERO:
        return
    post_journal(
        date=invoice.created_at.date() if invoice.created_at else date.today(),
        narration=f"Invoice {invoice.invoice_number}",
        source_type="invoice",
        source_id=invoice.id,
        lines=[
            {"account": "1100", "debit": total, "credit": 0},
            {"account": "4000", "debit": 0, "credit": total},
        ],
    )


def post_payment(payment) -> None:
    amount = _q(payment.amount)
    if amount <= ZERO:
        return
    post_journal(
        date=payment.paid_at.date() if getattr(payment, "paid_at", None) else date.today(),
        narration=f"Fee payment #{payment.id}",
        source_type="payment",
        source_id=payment.id,
        lines=[
            {"account": _cash_account(payment.method), "debit": amount, "credit": 0},
            {"account": "1100", "debit": 0, "credit": amount},
        ],
    )


def post_refund(refund) -> None:
    amount = _q(refund.amount)
    if amount <= ZERO:
        return
    post_journal(
        date=refund.created_at.date() if refund.created_at else date.today(),
        narration=f"Refund #{refund.id}",
        source_type="refund",
        source_id=refund.id,
        lines=[
            {"account": "1100", "debit": amount, "credit": 0},
            {"account": _cash_account(getattr(refund, "method", "")), "debit": 0, "credit": amount},
        ],
    )


def post_expense(expense) -> None:
    amount = _q(expense.amount)
    if amount <= ZERO:
        return
    method = getattr(expense, "payment_method", "")
    post_journal(
        date=getattr(expense, "expense_date", None) or date.today(),
        narration=f"Expense: {getattr(expense, 'title', '') or expense.category}",
        source_type="expense",
        source_id=expense.id,
        lines=[
            {"account": "5100", "debit": amount, "credit": 0},
            {"account": _cash_account(method), "debit": 0, "credit": amount},
        ],
    )


def post_transport_expense(expense) -> None:
    amount = _q(expense.amount)
    if amount <= ZERO:
        return
    post_journal(
        date=getattr(expense, "spent_on", None) or date.today(),
        narration=f"Transport: {expense.get_category_display()}",
        source_type="transport_expense",
        source_id=expense.id,
        lines=[
            {"account": "5300", "debit": amount, "credit": 0},
            {
                "account": _cash_account(getattr(expense, "payment_method", "")),
                "debit": 0,
                "credit": amount,
            },
        ],
    )


def post_payroll(payout) -> None:
    """Dr Salaries (gross), Cr Bank/Cash (net), Cr Statutory Dues (deductions)."""
    gross = _q(payout.base_amount) + _q(payout.bonus_amount)
    net = _q(payout.net_amount)
    deductions = _q(payout.deductions)
    if gross <= ZERO or net + deductions != gross:
        return
    lines = [
        {"account": "5000", "debit": gross, "credit": 0},
        {"account": _cash_account(payout.payment_method), "debit": 0, "credit": net},
    ]
    if deductions > ZERO:
        lines.append({"account": "2200", "debit": 0, "credit": deductions})
    post_journal(
        date=date.today(),
        narration=f"Salary payout #{payout.id} ({payout.pay_period})",
        source_type="payout",
        source_id=payout.id,
        lines=lines,
    )
