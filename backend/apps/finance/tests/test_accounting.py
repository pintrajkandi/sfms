"""Accounting sync exporters — Tally XML, Zoho & QuickBooks CSV rows."""

from datetime import date, timedelta

import pytest

from apps.finance import accounting

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


def _payment():
    from apps.collections.services import create_invoice, record_payment

    inv = create_invoice(
        student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    return record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="acct1")


def _expense():
    from apps.expenses.models import Expense

    return Expense.objects.create(
        title="Electricity", category="utilities", amount="300.00", expense_date=date.today()
    )


def _range():
    today = date.today()
    return today - timedelta(days=30), today


def test_tally_xml_has_receipt_and_payment_vouchers(tenant_ctx):
    _payment()
    _expense()
    since, until = _range()
    xml = accounting.tally_xml(since, until)
    assert "<ENVELOPE>" in xml
    assert 'VCHTYPE="Receipt"' in xml  # fee income
    assert 'VCHTYPE="Payment"' in xml  # expense
    assert "Fee Income" in xml


def test_zoho_rows_include_payment(tenant_ctx):
    _payment()
    since, until = _range()
    headers, rows = accounting.zoho_rows(since, until)
    assert "Customer Name" in headers
    assert len(rows) == 1
    assert rows[0][3] == "1000.00"  # amount column


def test_quickbooks_rows_sign_income_positive_expense_negative(tenant_ctx):
    _payment()
    _expense()
    since, until = _range()
    headers, rows = accounting.quickbooks_rows(since, until)
    amounts = [r[2] for r in rows]
    assert "1000.00" in amounts
    assert "-300.00" in amounts


def test_build_export_dispatch(tenant_ctx):
    _payment()
    since, until = _range()
    kind, name, payload = accounting.build_export("tally", since, until)
    assert kind == "xml" and name == "tally_vouchers"
    kind, name, payload = accounting.build_export("zoho", since, until)
    assert kind == "csv" and payload[0][0] == "Payment Number"
