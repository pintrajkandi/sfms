"""Route profitability: expected transport-fee income vs vehicle expenses."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Q, Sum

from apps.core.models import ZERO

from .models import TransportExpense, TransportRoute


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def route_profitability() -> dict:
    """Per route: riders × monthly fare (income) − transport expenses = profit."""
    rows = []
    total_income = total_expense = ZERO
    for route in TransportRoute.objects.prefetch_related("vehicles"):
        riders = route.students.count()
        income = route.monthly_fare * riders
        vehicle_ids = list(route.vehicles.values_list("id", flat=True))
        expense = (
            TransportExpense.objects.filter(
                Q(route=route) | Q(vehicle_id__in=vehicle_ids)
            ).aggregate(s=Sum("amount"))["s"]
            or ZERO
        )
        total_income += income
        total_expense += expense
        rows.append(
            {
                "route": route.name,
                "code": route.code,
                "riders": riders,
                "monthly_fare": _q(route.monthly_fare),
                "expected_income": _q(income),
                "expense": _q(expense),
                "profit": _q(income - expense),
            }
        )
    return {
        "routes": rows,
        "total_income": _q(total_income),
        "total_expense": _q(total_expense),
        "net": _q(total_income - total_expense),
    }
