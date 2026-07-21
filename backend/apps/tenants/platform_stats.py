"""
Cross-tenant platform metrics for the admin dashboard.

Aggregating across schemas is an N+1 by nature, so the whole payload is cached
(5 min). Called from the platform admin index and the ops panel.
"""

from __future__ import annotations

from datetime import date, timedelta

from django.core.cache import cache
from django.db.models import Sum
from django_tenants.utils import get_public_schema_name, tenant_context

_CACHE_KEY = "platform:stats"
_TTL = 300


def platform_stats(*, use_cache: bool = True) -> dict:
    if use_cache:
        cached = cache.get(_CACHE_KEY)
        if cached is not None:
            return cached

    from .models import Client

    public = get_public_schema_name()
    clients = Client.objects.exclude(schema_name=public)

    total = clients.count()
    active = clients.filter(is_active=True, is_archived=False).count()
    suspended = clients.filter(is_active=False).count()
    archived = clients.filter(is_archived=True).count()
    trial = clients.filter(on_trial=True, is_active=True, is_archived=False).count()
    paid = clients.filter(on_trial=False, is_active=True, is_archived=False).count()

    students = unverified = 0
    for client in clients.filter(is_active=True, is_archived=False):
        try:
            with tenant_context(client):
                from apps.accounts.models import User
                from apps.students.models import Student

                students += Student.objects.alive().count()
                unverified += User.objects.filter(email_verified=False).count()
        except Exception:
            continue

    today = date.today()
    soon = today + timedelta(days=14)
    expiring = clients.filter(
        paid_until__isnull=False, paid_until__gte=today, paid_until__lte=soon
    ).count()
    mrr = (
        clients.filter(is_active=True, on_trial=False, plan__isnull=False).aggregate(
            s=Sum("plan__price_monthly")
        )["s"]
        or 0
    )

    result = {
        "schools_total": total,
        "schools_active": active,
        "schools_suspended": suspended,
        "schools_archived": archived,
        "schools_trial": trial,
        "schools_paid": paid,
        "students_total": students,
        "verification_pending": unverified,
        "trials_expiring": expiring,
        "mrr": str(mrr),
    }
    cache.set(_CACHE_KEY, result, _TTL)
    return result


def invalidate() -> None:
    cache.delete(_CACHE_KEY)
