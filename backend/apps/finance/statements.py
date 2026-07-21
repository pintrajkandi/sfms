"""
Financial statements derived from the journal: Trial Balance, Profit & Loss,
Balance Sheet, and a per-account General Ledger. All read-only aggregates.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Sum

from apps.core.models import ZERO

from .models import Account, AccountType, JournalEntry, JournalLine


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def _balances(*, since=None, until=None) -> dict[int, dict]:
    """Sum debit/credit per account over an optional date window."""
    lines = JournalLine.objects.all()
    if since:
        lines = lines.filter(entry__date__gte=since)
    if until:
        lines = lines.filter(entry__date__lte=until)
    rows = lines.values("account_id").annotate(d=Sum("debit"), c=Sum("credit"))
    return {r["account_id"]: {"debit": r["d"] or ZERO, "credit": r["c"] or ZERO} for r in rows}


def trial_balance(*, as_of=None) -> dict:
    """Every account's net debit/credit. Total debits must equal total credits."""
    bal = _balances(until=as_of)
    accounts = Account.objects.all()
    rows, total_d, total_c = [], ZERO, ZERO
    for acc in accounts:
        b = bal.get(acc.id, {"debit": ZERO, "credit": ZERO})
        net = b["debit"] - b["credit"]
        debit = net if net > ZERO else ZERO
        credit = -net if net < ZERO else ZERO
        if debit == ZERO and credit == ZERO:
            continue
        total_d += debit
        total_c += credit
        rows.append(
            {
                "code": acc.code,
                "name": acc.name,
                "type": acc.type,
                "debit": _q(debit),
                "credit": _q(credit),
            }
        )
    return {
        "rows": rows,
        "total_debit": _q(total_d),
        "total_credit": _q(total_c),
        "balanced": total_d == total_c,
        "as_of": (as_of or date.today()).isoformat(),
    }


def profit_and_loss(*, since=None, until=None) -> dict:
    """Income − Expense over a window."""
    bal = _balances(since=since, until=until)
    income, expense = [], []
    total_income, total_expense = ZERO, ZERO
    for acc in Account.objects.filter(type__in=[AccountType.INCOME, AccountType.EXPENSE]):
        b = bal.get(acc.id, {"debit": ZERO, "credit": ZERO})
        if acc.type == AccountType.INCOME:
            amt = b["credit"] - b["debit"]
            total_income += amt
            if amt:
                income.append({"code": acc.code, "name": acc.name, "amount": _q(amt)})
        else:
            amt = b["debit"] - b["credit"]
            total_expense += amt
            if amt:
                expense.append({"code": acc.code, "name": acc.name, "amount": _q(amt)})
    return {
        "income": income,
        "expense": expense,
        "total_income": _q(total_income),
        "total_expense": _q(total_expense),
        "net_profit": _q(total_income - total_expense),
    }


def balance_sheet(*, as_of=None) -> dict:
    """Assets = Liabilities + Equity (+ retained earnings from net profit)."""
    bal = _balances(until=as_of)
    assets, liabilities, equity = [], [], []
    total_assets = total_liabilities = total_equity = ZERO
    total_income = total_expense = ZERO
    for acc in Account.objects.all():
        b = bal.get(acc.id, {"debit": ZERO, "credit": ZERO})
        debit_net = b["debit"] - b["credit"]
        credit_net = b["credit"] - b["debit"]
        if acc.type == AccountType.ASSET:
            total_assets += debit_net
            if debit_net:
                assets.append({"code": acc.code, "name": acc.name, "amount": _q(debit_net)})
        elif acc.type == AccountType.LIABILITY:
            total_liabilities += credit_net
            if credit_net:
                liabilities.append({"code": acc.code, "name": acc.name, "amount": _q(credit_net)})
        elif acc.type == AccountType.EQUITY:
            total_equity += credit_net
            if credit_net:
                equity.append({"code": acc.code, "name": acc.name, "amount": _q(credit_net)})
        elif acc.type == AccountType.INCOME:
            total_income += credit_net
        elif acc.type == AccountType.EXPENSE:
            total_expense += debit_net

    retained = total_income - total_expense
    if retained:
        equity.append(
            {"code": "3900", "name": "Retained Earnings (current)", "amount": _q(retained)}
        )
        total_equity += retained

    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": _q(total_assets),
        "total_liabilities": _q(total_liabilities),
        "total_equity": _q(total_equity),
        "balanced": total_assets == (total_liabilities + total_equity),
        "as_of": (as_of or date.today()).isoformat(),
    }


def day_book(*, since=None, until=None) -> dict:
    """Every journal entry (with its lines) over a window, newest first."""
    entries = JournalEntry.objects.prefetch_related("lines__account")
    if since:
        entries = entries.filter(date__gte=since)
    if until:
        entries = entries.filter(date__lte=until)
    entries = entries.order_by("-date", "-id")[:500]
    total_debit = total_credit = ZERO
    out = []
    for e in entries:
        lines = []
        for ln in e.lines.all():
            total_debit += ln.debit
            total_credit += ln.credit
            lines.append(
                {
                    "account": f"{ln.account.code} · {ln.account.name}",
                    "debit": _q(ln.debit),
                    "credit": _q(ln.credit),
                }
            )
        out.append(
            {"id": e.id, "date": e.date.isoformat(), "narration": e.narration, "lines": lines}
        )
    return {"entries": out, "total_debit": _q(total_debit), "total_credit": _q(total_credit)}


def general_ledger(*, account_code: str, since=None, until=None) -> dict:
    """Per-account line history with a running balance."""
    acc = Account.objects.filter(code=account_code).first()
    if acc is None:
        return {"account": None, "lines": []}
    lines = JournalLine.objects.filter(account=acc).select_related("entry")
    if since:
        lines = lines.filter(entry__date__gte=since)
    if until:
        lines = lines.filter(entry__date__lte=until)
    lines = lines.order_by("entry__date", "id")
    sign = 1 if acc.type in (AccountType.ASSET, AccountType.EXPENSE) else -1
    running = ZERO
    out = []
    for ln in lines:
        running += sign * (ln.debit - ln.credit)
        out.append(
            {
                "date": ln.entry.date.isoformat(),
                "narration": ln.entry.narration,
                "debit": _q(ln.debit),
                "credit": _q(ln.credit),
                "balance": _q(running),
            }
        )
    return {
        "account": {"code": acc.code, "name": acc.name, "type": acc.type},
        "lines": out,
        "closing_balance": _q(running),
    }
