"""Money math + payment idempotency (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.collections.models import InvoiceStatus
from apps.collections.services import create_invoice, record_payment
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def test_invoice_totals_use_decimal(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(
        student=student,
        lines=[{"fee_type": ft, "quantity": 2, "unit_price": "500.00"}],
        discount_amount="100.00",
        late_fee_amount="50.00",
    )
    assert inv.subtotal == Decimal("1000.00")
    assert inv.total == Decimal("950.00")  # 1000 - 100 + 50
    assert inv.status == InvoiceStatus.PENDING


def test_partial_then_full_payment_transitions_status(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])

    record_payment(invoice=inv, amount="400.00", method="cash", idempotency_key="k1")
    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PARTIAL
    assert inv.amount_paid == Decimal("400.00")

    record_payment(invoice=inv, amount="600.00", method="cash", idempotency_key="k2")
    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID
    assert inv.balance == Decimal("0.00")


def test_payment_is_idempotent(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])

    p1 = record_payment(invoice=inv, amount="500.00", method="cash", idempotency_key="dup")
    p2 = record_payment(invoice=inv, amount="500.00", method="cash", idempotency_key="dup")

    assert p1.id == p2.id  # same payment, not double-charged
    inv.refresh_from_db()
    assert inv.amount_paid == Decimal("500.00")


def test_payment_serializer_paid_at_optional(tenant_ctx):
    from apps.collections.serializers import PaymentSerializer

    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "100.00"}])
    serializer = PaymentSerializer(data={"invoice": inv.id, "amount": "100.00", "method": "paypal"})
    assert serializer.is_valid(), serializer.errors  # paid_at optional, paypal valid


def test_overpayment_rejected(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "100.00"}])
    with pytest.raises(ServiceError):
        record_payment(invoice=inv, amount="150.00", method="cash", idempotency_key="over")
