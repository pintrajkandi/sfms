"""Route profitability = riders × fare − transport expenses."""

from datetime import date

import pytest

from apps.transport.models import TransportExpense, TransportRoute, Vehicle
from apps.transport.selectors import route_profitability

pytestmark = [pytest.mark.django_db]


def _student(route, **kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Rider")
    kw.setdefault("last_name", "One")
    student = create_student(**kw)
    student.transport_route = route
    student.save(update_fields=["transport_route"])
    return student


def test_route_profitability(tenant_ctx):
    route = TransportRoute.objects.create(name="North", code="R-N", monthly_fare="1000.00")
    vehicle = Vehicle.objects.create(registration_number="KA01AB1234", route=route)
    _student(route, first_name="A")
    _student(route, first_name="B")
    _student(route, first_name="C")
    # Two expenses: one tagged to the route, one to its vehicle.
    TransportExpense.objects.create(
        route=route, category="fuel", amount="1200.00", spent_on=date.today()
    )
    TransportExpense.objects.create(
        vehicle=vehicle, category="maintenance", amount="800.00", spent_on=date.today()
    )

    report = route_profitability()
    row = next(r for r in report["routes"] if r["code"] == "R-N")
    assert row["riders"] == 3
    assert row["expected_income"] == "3000.00"  # 3 × 1000
    assert row["expense"] == "2000.00"  # 1200 + 800
    assert row["profit"] == "1000.00"
    assert report["net"] == "1000.00"
