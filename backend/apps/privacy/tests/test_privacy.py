"""Data-subject rights: export, erasure, consent, retention (CLAUDE.md §8)."""

import datetime

import pytest
from django.utils import timezone

from apps.privacy import services
from apps.privacy.models import ConsentRecord, DataSubjectRequest

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    kw.setdefault("email", "ada@example.com")
    kw.setdefault("guardian_phone", "+91 90000 11111")
    return create_student(**kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat, _ = FeeCategory.objects.get_or_create(name="Academic")
    ft, _ = FeeType.objects.get_or_create(
        name="Tuition", defaults={"category": cat, "default_amount": "1000.00"}
    )
    return ft


def test_export_includes_personal_and_financial(tenant_ctx):
    from apps.collections.services import create_invoice, record_payment

    student = _student()
    inv = create_invoice(
        student=student, lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    record_payment(invoice=inv, amount="500.00", method="cash", idempotency_key="px1")

    data = services.export_student_data(student)
    assert data["personal"]["first_name"] == "Ada"
    assert data["contact"]["email"] == "ada@example.com"
    assert len(data["financial"]["invoices"]) == 1
    assert len(data["financial"]["payments"]) == 1


def test_erasure_anonymizes_pii_keeps_financial(tenant_ctx):
    from apps.collections.models import Payment
    from apps.collections.services import create_invoice, record_payment

    student = _student()
    inv = create_invoice(
        student=student, lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="px2")

    req = services.erase_student_data(student, reason="parent request")
    student.refresh_from_db()

    # PII gone, id + financial intact
    assert student.first_name == "Redacted"
    assert student.email == ""
    assert student.guardian_phone == ""
    assert student.student_id  # keeps stable id
    assert Payment.objects.filter(invoice__student=student).count() == 1
    assert req.kind == DataSubjectRequest.Kind.ERASURE
    assert req.status == DataSubjectRequest.Status.COMPLETED
    assert "Lovelace" in req.subject_label  # snapshot survives erasure


def test_erasure_is_idempotent(tenant_ctx):
    student = _student()
    services.erase_student_data(student)
    services.erase_student_data(student)  # no crash
    student.refresh_from_db()
    assert student.first_name == "Redacted"


def test_consent_upsert(tenant_ctx):
    student = _student()
    services.record_consent(student=student, purpose="marketing", granted=True)
    services.record_consent(student=student, purpose="marketing", granted=False)  # withdraw
    rows = ConsentRecord.objects.filter(student=student, purpose="marketing")
    assert rows.count() == 1  # upsert, not duplicate
    assert rows.first().granted is False


def test_retention_sweep_erases_old_leavers(tenant_ctx):
    from apps.students.models import EnrollmentStatus

    old = _student(first_name="Grad", last_name="Uate")
    old.status = EnrollmentStatus.GRADUATED
    old.enrollment_date = timezone.now().date() - datetime.timedelta(days=4000)
    old.save()
    recent = _student(first_name="Still", last_name="Here")

    result = services.run_retention(anonymize_after_days=2555)
    assert result["erased"] == 1
    old.refresh_from_db()
    recent.refresh_from_db()
    assert old.first_name == "Redacted"
    assert recent.first_name == "Still"  # active student untouched
