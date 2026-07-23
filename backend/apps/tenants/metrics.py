"""
Cross-school platform metrics for the SaaS operator (public schema).

Registry metrics (schools, MRR, growth, renewals, plan mix) come from the public
Client/Plan tables. Collections/expenses aggregate across tenant schemas, so the
whole result is cached briefly to keep the dashboard cheap.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache

from apps.core.models import ZERO

_CACHE_KEY = "platform:metrics"
_TTL = 300  # 5 minutes


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def _month_keys(months: int) -> list[str]:
    today = date.today().replace(day=1)
    keys = []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        keys.append(f"{y:04d}-{m:02d}")
    return keys


def platform_metrics(*, use_cache: bool = True) -> dict:
    if use_cache:
        cached = cache.get(_CACHE_KEY)
        if cached is not None:
            return cached

    from apps.tenants.models import Client

    schools = Client.objects.exclude(schema_name="public")
    active = schools.filter(is_active=True, is_archived=False)
    total = schools.count()
    active_count = active.count()
    trial_count = active.filter(on_trial=True).count()
    archived_count = schools.filter(is_archived=True).count()

    # MRR = sum of active schools' monthly-equivalent plan price.
    mrr = ZERO
    plan_mix: dict[str, int] = {}
    for client in active.select_related("plan"):
        plan = client.plan
        name = plan.name if plan else "None"
        plan_mix[name] = plan_mix.get(name, 0) + 1
        if plan and plan.price_monthly:
            price = plan.price_monthly
            if plan.interval == "yearly":
                price = price / 12
            mrr += price

    # Growth: new schools per month.
    created_by = {}
    for client in schools:
        key = client.created_on.strftime("%Y-%m") if client.created_on else None
        if key:
            created_by[key] = created_by.get(key, 0) + 1
    growth = [{"month": k, "new_schools": created_by.get(k, 0)} for k in _month_keys(6)]

    # Renewals due in the next 30 days.
    soon = date.today() + timedelta(days=30)
    renewals_due = schools.filter(
        paid_until__isnull=False, paid_until__lte=soon, paid_until__gte=date.today()
    ).count()

    # Registry-only metrics — the platform operator does NOT read into any
    # school's schema (their collections/expenses stay private to the school).
    result = {
        "active_schools": active_count,
        "trial_schools": trial_count,
        "paid_schools": active_count - trial_count,
        "archived_schools": archived_count,
        "total_schools": total,
        "mrr": _q(mrr),
        "arr": _q(mrr * 12),
        "renewals_due_30d": renewals_due,
        "plan_mix": [{"plan": k, "count": v} for k, v in sorted(plan_mix.items())],
        "growth": growth,
    }
    cache.set(_CACHE_KEY, result, _TTL)
    return result
