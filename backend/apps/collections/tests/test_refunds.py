"""Refunds (cash out) & credit notes (reduce bill) — money math + guards."""

from decimal import Decimal

import pytest

from apps.collections.models import CreditNote, InvoiceStatus, Refund
from apps.collections.services import (
    create_invoice,
    issue_credit_note,
    record_payment,
    record_refund,
)
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def _paid_invoice(unit="1000.00", pay="1000.00"):
    inv = create_invoice(student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": unit}])
    record_payment(invoice=inv, amount=pay, method="cash", idempotency_key=f"pay-{inv.id}")
    inv.refresh_from_db()
    return inv


# --- refunds ---------------------------------------------------------------


def test_refund_reduces_amount_paid_and_status(tenant_ctx):
    inv = _paid_invoice()
    assert inv.status == InvoiceStatus.PAID

    record_refund(invoice=inv, amount="400.00", method="cash", idempotency_key="r1")
    inv.refresh_from_db()
    assert inv.amount_paid == Decimal("600.00")
    assert inv.status == InvoiceStatus.PARTIAL
    assert inv.balance == Decimal("400.00")


def test_refund_is_idempotent(tenant_ctx):
    inv = _paid_invoice()
    r1 = record_refund(invoice=inv, amount="200.00", method="cash", idempotency_key="dup")
    r2 = record_refund(invoice=inv, amount="200.00", method="cash", idempotency_key="dup")
    assert r1.id == r2.id
    inv.refresh_from_db()
    assert inv.amount_paid == Decimal("800.00")  # refunded once


def test_refund_cannot_exceed_amount_paid(tenant_ctx):
    inv = _paid_invoice(pay="300.00")  # partial
    with pytest.raises(ServiceError):
        record_refund(invoice=inv, amount="400.00", method="cash", idempotency_key="over")


def test_refund_rejects_non_positive(tenant_ctx):
    inv = _paid_invoice()
    with pytest.raises(ServiceError):
        record_refund(invoice=inv, amount="0.00", method="cash", idempotency_key="zero")


# --- credit notes ----------------------------------------------------------


def test_credit_note_reduces_total_no_cash(tenant_ctx):
    inv = create_invoice(
        student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    note = issue_credit_note(invoice=inv, amount="150.00", kind="write_off", reason="goodwill")
    inv.refresh_from_db()
    assert note.credit_note_number.startswith("CN-")
    assert inv.adjustment_amount == Decimal("150.00")
    assert inv.total == Decimal("850.00")
    assert inv.amount_paid == Decimal("0.00")  # no cash moved


def test_credit_note_can_settle_remaining_balance(tenant_ctx):
    inv = _paid_invoice(pay="700.00")  # 300 outstanding
    issue_credit_note(invoice=inv, amount="300.00", kind="adjustment")
    inv.refresh_from_db()
    assert inv.total == Decimal("700.00")
    assert inv.balance == Decimal("0.00")
    assert inv.status == InvoiceStatus.PAID


def test_credit_note_cannot_exceed_balance(tenant_ctx):
    inv = _paid_invoice(pay="900.00")  # 100 outstanding
    with pytest.raises(ServiceError):
        issue_credit_note(invoice=inv, amount="200.00")


def test_credit_note_numbers_increment(tenant_ctx):
    inv = create_invoice(
        student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    n1 = issue_credit_note(invoice=inv, amount="100.00")
    n2 = issue_credit_note(invoice=inv, amount="100.00")
    assert n1.credit_note_number != n2.credit_note_number
    assert CreditNote.objects.count() == 2
    assert Refund.objects.count() == 0
