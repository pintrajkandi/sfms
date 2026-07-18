"""Instalment / payment-plan schedule + allocation (CLAUDE.md §8)."""

import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.collections.models import Installment, PaymentPlan
from apps.collections.services import create_invoice, create_payment_plan, record_payment
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def _invoice(unit="900.00"):
    return create_invoice(student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": unit}])


def test_even_split_creates_installments_summing_to_total(tenant_ctx):
    inv = _invoice("1000.00")
    plan = create_payment_plan(invoice=inv, count=3, first_due_date=timezone.now().date())
    insts = list(plan.installments.order_by("sequence"))
    assert len(insts) == 3
    assert sum(i.amount for i in insts) == Decimal("1000.00")
    # remainder rides the last instalment
    assert insts[0].amount == Decimal("333.33")
    assert insts[-1].amount == Decimal("333.34")


def test_explicit_schedule_must_sum_to_total(tenant_ctx):
    inv = _invoice("1000.00")
    today = timezone.now().date()
    with pytest.raises(ServiceError):
        create_payment_plan(
            invoice=inv,
            schedule=[
                {"due_date": today, "amount": "400.00"},
                {"due_date": today, "amount": "500.00"},  # sums to 900, not 1000
            ],
        )


def test_duplicate_plan_rejected(tenant_ctx):
    inv = _invoice("1000.00")
    create_payment_plan(invoice=inv, count=2, first_due_date=timezone.now().date())
    with pytest.raises(ServiceError):
        create_payment_plan(invoice=inv, count=2, first_due_date=timezone.now().date())


def test_payment_waterfalls_across_installments(tenant_ctx):
    inv = _invoice("1000.00")
    create_payment_plan(invoice=inv, count=4, first_due_date=timezone.now().date())  # 250 each

    record_payment(invoice=inv, amount="600.00", method="cash", idempotency_key="p1")
    inv.refresh_from_db()
    insts = list(inv.payment_plan.installments.order_by("sequence"))
    assert insts[0].status == Installment.Status.PAID
    assert insts[1].status == Installment.Status.PAID
    assert insts[2].amount_paid == Decimal("100.00")
    assert insts[2].status == Installment.Status.PARTIAL
    assert insts[3].amount_paid == Decimal("0.00")


def test_full_payment_completes_plan(tenant_ctx):
    inv = _invoice("1000.00")
    plan = create_payment_plan(invoice=inv, count=2, first_due_date=timezone.now().date())

    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="full")
    plan.refresh_from_db()
    assert plan.status == PaymentPlan.Status.COMPLETED
    assert all(i.status == Installment.Status.PAID for i in plan.installments.all())


def test_overdue_installment_flagged(tenant_ctx):
    inv = _invoice("1000.00")
    past = timezone.now().date() - datetime.timedelta(days=30)
    plan = create_payment_plan(invoice=inv, count=2, first_due_date=past)
    # nothing paid; first instalment's due date is in the past
    first = plan.installments.order_by("sequence").first()
    assert first.status == Installment.Status.OVERDUE
