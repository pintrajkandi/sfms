"""Defaulter / aging report (CLAUDE.md §8)."""
from datetime import date, timedelta

import pytest

from apps.collections.selectors import defaulter_report
from apps.collections.services import create_invoice, record_payment

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", grade="Grade 9", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def test_defaulter_report_buckets_by_days_overdue(tenant_ctx):
    student, ft = _student(), _fee_type()
    create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": "1000.00"}],
        due_date=date.today() - timedelta(days=45),  # 45 days overdue -> "31-60"
    )
    report = defaulter_report()
    assert report["count"] == 1
    row = report["defaulters"][0]
    assert row["bucket"] == "31-60"
    assert row["days_overdue"] == 45
    assert row["outstanding"] == "1000.00"


def test_paid_invoice_not_a_defaulter(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "500.00"}])
    record_payment(invoice=inv, amount="500.00", method="cash", idempotency_key="k1")
    assert defaulter_report()["count"] == 0
