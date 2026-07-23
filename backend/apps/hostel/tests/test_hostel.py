"""Hostel report: residents × fee − expenses = profit, plus occupancy."""

from datetime import date

import pytest

from apps.hostel.models import Hostel, HostelExpense
from apps.hostel.selectors import hostel_report

pytestmark = [pytest.mark.django_db]


def _resident(hostel, **kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Res")
    kw.setdefault("last_name", "Ident")
    student = create_student(**kw)
    student.hostel = hostel
    student.save(update_fields=["hostel"])
    return student


def test_hostel_report(tenant_ctx):
    hostel = Hostel.objects.create(name="Boys A", code="H-A", monthly_fee="2000.00", capacity=4)
    _resident(hostel, first_name="X")
    _resident(hostel, first_name="Y")
    HostelExpense.objects.create(
        hostel=hostel, category="mess", amount="1500.00", spent_on=date.today()
    )

    report = hostel_report()
    row = next(r for r in report["hostels"] if r["code"] == "H-A")
    assert row["residents"] == 2
    assert row["capacity"] == 4
    assert row["occupancy_percent"] == 50.0
    assert row["expected_income"] == "4000.00"  # 2 × 2000
    assert row["expense"] == "1500.00"
    assert row["profit"] == "2500.00"
    assert report["net"] == "2500.00"
