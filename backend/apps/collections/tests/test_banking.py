"""Bank reconciliation + cheque-bounce (CLAUDE.md §8)."""

from decimal import Decimal

import pytest
from django.utils import timezone

from apps.collections.banking import auto_reconcile, bounce_cheque, import_bank_statement
from apps.collections.models import BankStatementLine, InvoiceStatus, Payment
from apps.collections.services import create_invoice, record_payment
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def _invoice():
    return create_invoice(
        student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )


def test_reconcile_matches_by_reference(tenant_ctx):
    inv = _invoice()
    record_payment(
        invoice=inv,
        amount="1000.00",
        method="bank_transfer",
        idempotency_key="bt1",
        reference="UTR12345",
    )
    stmt = import_bank_statement(
        label="July",
        account_ref="1234",
        rows=[{"txn_date": timezone.now().date(), "reference": "UTR12345", "amount": "1000.00"}],
    )
    result = auto_reconcile(statement=stmt)
    assert result["matched"] == 1
    assert result["unmatched"] == 0
    line = stmt.lines.first()
    assert line.status == BankStatementLine.Status.MATCHED
    assert line.payment is not None


def test_reconcile_matches_by_date_when_no_reference(tenant_ctx):
    inv = _invoice()
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="c1")
    stmt = import_bank_statement(
        label="July",
        account_ref="1234",
        rows=[{"txn_date": timezone.now().date(), "amount": "1000.00"}],
    )
    assert auto_reconcile(statement=stmt)["matched"] == 1


def test_reconcile_leaves_unmatched_when_no_payment(tenant_ctx):
    stmt = import_bank_statement(
        label="July",
        account_ref="1234",
        rows=[{"txn_date": timezone.now().date(), "amount": "555.00"}],
    )
    result = auto_reconcile(statement=stmt)
    assert result["matched"] == 0
    assert result["unmatched"] == 1


def test_debit_lines_are_not_matched(tenant_ctx):
    inv = _invoice()
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="c2")
    stmt = import_bank_statement(
        label="July",
        account_ref="1234",
        rows=[{"txn_date": timezone.now().date(), "amount": "-1000.00"}],  # debit
    )
    assert auto_reconcile(statement=stmt)["matched"] == 0


def test_cheque_bounce_reverses_credit(tenant_ctx):
    inv = _invoice()
    pay = record_payment(invoice=inv, amount="1000.00", method="cheque", idempotency_key="chq1")
    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID

    bounce_cheque(payment=pay, reason="insufficient funds")
    inv.refresh_from_db()
    pay.refresh_from_db()
    assert pay.status == Payment.Status.VOID
    assert inv.amount_paid == Decimal("0.00")
    assert inv.status in (InvoiceStatus.PENDING, InvoiceStatus.OVERDUE)


def test_cheque_bounce_with_charge_adds_late_fee(tenant_ctx):
    inv = _invoice()
    pay = record_payment(invoice=inv, amount="1000.00", method="cheque", idempotency_key="chq2")
    bounce_cheque(payment=pay, reason="stop payment", charge="250.00")
    inv.refresh_from_db()
    # original 1000 reversed; total now 1000 + 250 late fee
    assert inv.late_fee_amount == Decimal("250.00")
    assert inv.total == Decimal("1250.00")


def test_cannot_bounce_twice(tenant_ctx):
    inv = _invoice()
    pay = record_payment(invoice=inv, amount="1000.00", method="cheque", idempotency_key="chq3")
    bounce_cheque(payment=pay)
    with pytest.raises(ServiceError):
        bounce_cheque(payment=pay)
