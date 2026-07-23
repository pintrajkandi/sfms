"""Hostel occupancy + profitability: fee income vs hostel expenses."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Sum

from apps.core.models import ZERO

from .models import Hostel, HostelExpense


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def hostel_report() -> dict:
    """Per hostel: residents × monthly fee (income) − expenses = profit + occupancy."""
    rows = []
    total_income = total_expense = ZERO
    total_capacity = total_residents = 0
    for hostel in Hostel.objects.all():
        residents = hostel.residents.count()
        income = hostel.monthly_fee * residents
        expense = (
            HostelExpense.objects.filter(hostel=hostel).aggregate(s=Sum("amount"))["s"] or ZERO
        )
        total_income += income
        total_expense += expense
        total_capacity += hostel.capacity
        total_residents += residents
        occupancy = round(residents / hostel.capacity * 100, 1) if hostel.capacity else 0.0
        rows.append(
            {
                "hostel": hostel.name,
                "code": hostel.code,
                "residents": residents,
                "capacity": hostel.capacity,
                "occupancy_percent": occupancy,
                "monthly_fee": _q(hostel.monthly_fee),
                "expected_income": _q(income),
                "expense": _q(expense),
                "profit": _q(income - expense),
            }
        )
    return {
        "hostels": rows,
        "total_income": _q(total_income),
        "total_expense": _q(total_expense),
        "net": _q(total_income - total_expense),
        "total_residents": total_residents,
        "total_capacity": total_capacity,
    }
