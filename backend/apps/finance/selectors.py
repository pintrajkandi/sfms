"""
Finance/accounts dashboard aggregation — cached per tenant (CLAUDE.md §5 caching).

Income is real fee **payments**; expenses are **Expense** records. This keeps the
accounts view consistent with what's actually collected and spent.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from apps.collections.models import Payment
from apps.core.models import ZERO
from apps.expenses.models import Expense

_CACHE_TTL = 300
_CACHE_KEY = "finance:dashboard"


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def _month_keys(months: int) -> list[str]:
    today = date.today().replace(day=1)
    keys = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        keys.append(f"{y:04d}-{m:02d}")
    return keys


def dashboard_overview(*, months: int = 6, use_cache: bool = True) -> dict:
    if use_cache:
        cached = cache.get(_CACHE_KEY)
        if cached is not None:
            return cached

    since = date.today() - timedelta(days=months * 31)
    pay = Payment.objects.filter(paid_at__date__gte=since)
    exp = Expense.objects.filter(expense_date__gte=since)

    total_income = pay.aggregate(s=Sum("amount"))["s"] or ZERO
    total_expense = exp.aggregate(s=Sum("amount"))["s"] or ZERO
    net = total_income - total_expense

    inc_by_month = {
        r["m"].strftime("%Y-%m"): r["s"]
        for r in pay.annotate(m=TruncMonth("paid_at")).values("m").annotate(s=Sum("amount"))
    }
    exp_by_month = {
        r["m"].strftime("%Y-%m"): r["s"]
        for r in exp.annotate(m=TruncMonth("expense_date")).values("m").annotate(s=Sum("amount"))
    }

    monthly, running, trend = [], Decimal(0), []
    for key in _month_keys(months):
        inc = inc_by_month.get(key, ZERO)
        ex = exp_by_month.get(key, ZERO)
        monthly.append({"month": key, "income": _q(inc), "expense": _q(ex)})
        running += inc - ex
        trend.append({"month": key, "balance": _q(running)})

    expense_breakdown = [
        {"category": r["category"], "total": _q(r["s"])}
        for r in exp.values("category").annotate(s=Sum("amount")).order_by("-s")
    ]

    # Recent transactions — payments (income) and expenses, merged newest-first.
    txns = []
    for p in pay.select_related("invoice__student").order_by("-paid_at")[:10]:
        txns.append(
            {
                "title": getattr(p.invoice.student, "full_name", "Fee Payment"),
                "category": "Income",
                "date": p.paid_at.date().isoformat(),
                "amount": _q(p.amount),
                "direction": "in",
            }
        )
    for e in exp.order_by("-expense_date")[:10]:
        txns.append(
            {
                "title": e.title,
                "category": e.get_category_display(),
                "date": e.expense_date.isoformat(),
                "amount": _q(e.amount),
                "direction": "out",
            }
        )
    txns.sort(key=lambda t: t["date"], reverse=True)

    result = {
        "total_balance": _q(net),
        "total_income": _q(total_income),
        "total_expense": _q(total_expense),
        "net_savings": _q(net),
        "savings_rate_percent": round(float(net / total_income * 100), 1)
        if total_income > ZERO
        else 0.0,
        "monthly": monthly,
        "net_savings_trend": trend,
        "expense_breakdown": expense_breakdown,
        "recent_transactions": txns[:8],
    }
    if use_cache:
        cache.set(_CACHE_KEY, result, _CACHE_TTL)
    return result


def invalidate_dashboard() -> None:
    cache.delete(_CACHE_KEY)
