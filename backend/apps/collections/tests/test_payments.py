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


def test_annual_fee_drives_paid_and_outstanding(tenant_ctx):
    from apps.collections.selectors import student_fee_summary

    student = _student()
    student.tuition_fee = Decimal("1000.00")
    student.transport_fee = Decimal("500.00")
    student.save(update_fields=["tuition_fee", "transport_fee"])

    summary = student_fee_summary(student)
    assert summary["annual_fee"] == "1500.00"
    assert summary["total_fee"] == "1500.00"
    assert summary["outstanding"] == "1500.00"  # nothing paid yet

    # A payment reduces the outstanding against the assigned annual fee.
    inv = create_invoice(student=student, lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}])
    record_payment(invoice=inv, amount="400.00", method="cash", idempotency_key="af1")

    summary = student_fee_summary(student)
    assert summary["paid"] == "400.00"
    assert summary["outstanding"] == "1100.00"


def test_receipt_number_auto_generated_and_numeric(tenant_ctx):
    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])

    p = record_payment(invoice=inv, amount="500.00", method="upi", idempotency_key="rn1")
    assert p.receipt_number  # populated
    assert p.receipt_number.isdigit()  # purely numeric

    # The rendered receipt uses the numeric number, not the legacy composite form.
    from apps.collections.receipts import receipt_number

    assert receipt_number(p) == p.receipt_number
    assert "-R" not in receipt_number(p)
