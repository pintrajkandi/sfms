"""Audit trail — services record who-changed-what (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.core.audit import record_audit
from apps.core.models import AuditLog

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


def test_record_audit_writes_row_with_actor_label(tenant_ctx):
    entry = record_audit(action="test.event", summary="hello", actor=None)
    assert entry is not None
    assert entry.action == "test.event"
    assert entry.actor_label == "system"  # no actor → system


def test_invoice_and_payment_are_audited(tenant_ctx):
    from apps.collections.services import create_invoice, record_payment

    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    record_payment(invoice=inv, amount="400.00", method="cash", idempotency_key="a1")

    actions = set(AuditLog.objects.values_list("action", flat=True))
    assert "invoice.created" in actions
    assert "payment.recorded" in actions

    inv_audit = AuditLog.objects.filter(action="invoice.created").first()
    assert inv_audit.entity_type == "Invoice"
    assert inv_audit.entity_id == str(inv.id)


def test_refund_and_credit_note_audited(tenant_ctx):
    from apps.collections.services import (
        create_invoice,
        issue_credit_note,
        record_payment,
        record_refund,
    )

    student, ft = _student(), _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="a2")
    record_refund(invoice=inv, amount="200.00", method="cash", idempotency_key="ar1")
    inv.refresh_from_db()
    issue_credit_note(invoice=inv, amount="100.00")

    actions = set(AuditLog.objects.values_list("action", flat=True))
    assert {"refund.processed", "credit_note.issued"} <= actions


def test_payout_transition_audited(tenant_ctx):
    from apps.staff.models import Teacher
    from apps.staff.services import create_payout, transition_payout

    teacher = Teacher.objects.create(
        employee_id="EMP-1", first_name="Grace", last_name="H", base_salary="5000.00"
    )
    payout = create_payout(teacher=teacher, base_amount="5000.00", pay_period="2026-07")
    transition_payout(payout=payout, to_status="processed")
    assert AuditLog.objects.filter(action="payout.transition").exists()


def test_audit_never_raises_on_bad_entity(tenant_ctx):
    # A missing entity must not blow up the caller.
    entry = record_audit(action="test.noentity", entity=None, summary="ok")
    assert entry.entity_type == ""
    assert entry.entity_id == ""


def test_decimal_change_diff_stored(tenant_ctx):
    entry = record_audit(
        action="test.change", summary="changed", changes={"amount": ["100.00", "200.00"]}
    )
    assert entry.changes["amount"] == ["100.00", "200.00"]
    assert isinstance(Decimal(entry.changes["amount"][1]), Decimal)
