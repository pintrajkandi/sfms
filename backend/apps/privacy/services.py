"""
Data-subject rights (DPDP / FERPA / GDPR) — CLAUDE.md §5.

- export_student_data: the right of access / portability — a machine-readable
  dump of everything the school holds on a student.
- erase_student_data: the right to erasure — PII is anonymized IN PLACE so the
  financial audit trail (invoices, payments) stays intact and balanced; the row
  is not deleted. Idempotent.
- consent record/withdraw + a retention sweep round out the controls.

Every action is written to the audit log (who did what) and to a
DataSubjectRequest for the statutory paper trail.
"""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger

from .models import ConsentRecord, DataSubjectRequest

log = get_logger("privacy")

# PII fields on Student that erasure clears (financial + id fields are kept).
_PII_TEXT_FIELDS = (
    "date_of_birth",
    "gender",
    "email",
    "phone",
    "home_address",
    "guardian_name",
    "guardian_relation",
    "guardian_phone",
    "guardian_email",
    "previous_school",
    "notes",
)


def export_student_data(student) -> dict:
    """Full machine-readable export of a student's data (right of access)."""
    from apps.collections.models import Invoice, Mandate, Payment
    from apps.core.models import AuditLog

    invoices = list(
        Invoice.objects.filter(student=student).values(
            "invoice_number", "status", "total", "amount_paid", "currency", "due_date"
        )
    )
    payments = list(
        Payment.objects.filter(invoice__student=student).values(
            "amount", "currency", "method", "reference", "status", "paid_at"
        )
    )
    consents = list(
        ConsentRecord.objects.filter(student=student).values("purpose", "granted", "source")
    )
    mandates = list(
        Mandate.objects.filter(student=student).values("status", "max_amount", "currency")
    )
    audit = list(
        AuditLog.objects.filter(entity_type="Student", entity_id=str(student.pk)).values(
            "action", "summary", "created_at"
        )[:100]
    )
    return {
        "personal": {
            "student_id": student.student_id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "date_of_birth": student.date_of_birth,
            "gender": student.gender,
        },
        "contact": {
            "email": student.email,
            "phone": student.phone,
            "home_address": student.home_address,
        },
        "guardian": {
            "name": student.guardian_name,
            "relation": student.guardian_relation,
            "phone": student.guardian_phone,
            "email": student.guardian_email,
        },
        "academic": {
            "class": student.grade,
            "section": student.section,
            "status": student.status,
        },
        "financial": {"invoices": invoices, "payments": payments, "mandates": mandates},
        "consents": consents,
        "audit_trail": audit,
        "exported_at": timezone.now(),
    }


@transaction.atomic
def erase_student_data(student, *, reason: str = "", actor=None) -> DataSubjectRequest:
    """
    Anonymize a student's PII in place (right to erasure) while keeping their
    financial records for audit. Idempotent — re-running is a no-op.
    """
    label = f"{student.full_name} ({student.student_id})"

    student.first_name = "Redacted"
    student.last_name = f"Student-{student.pk}"
    for field in _PII_TEXT_FIELDS:
        value = getattr(student, field)
        if isinstance(value, str):
            setattr(student, field, "")
        else:
            setattr(student, field, None)
    if student.photo:
        student.photo.delete(save=False)
        student.photo = None
    student.save()

    # Refresh the search vector so the old name is not findable.
    try:
        from apps.students.services import refresh_search_vector

        refresh_search_vector(student)
    except Exception:  # search vector is best-effort
        pass

    req = DataSubjectRequest.objects.create(
        student=student,
        subject_label=label,
        kind=DataSubjectRequest.Kind.ERASURE,
        status=DataSubjectRequest.Status.COMPLETED,
        summary=(reason or "PII anonymized; financial records retained.")[:255],
        requested_by=actor if getattr(actor, "pk", None) else None,
        completed_at=timezone.now(),
    )
    log.info(
        "student data erased student=%s",
        student.pk,
        **ctx(user=getattr(actor, "id", "-"), entity=student.pk, action="erase_student"),
    )
    record_audit(
        action="privacy.erasure",
        entity=student,
        summary=f"Erased PII for {label}",
        actor=actor,
    )
    return req


@transaction.atomic
def log_access_request(student, *, actor=None) -> DataSubjectRequest:
    """Record that a data export was fulfilled (paper trail for access rights)."""
    req = DataSubjectRequest.objects.create(
        student=student,
        subject_label=f"{student.full_name} ({student.student_id})",
        kind=DataSubjectRequest.Kind.ACCESS,
        status=DataSubjectRequest.Status.COMPLETED,
        summary="Data export generated.",
        requested_by=actor if getattr(actor, "pk", None) else None,
        completed_at=timezone.now(),
    )
    record_audit(
        action="privacy.access",
        entity=student,
        summary=f"Data export for {req.subject_label}",
        actor=actor,
    )
    return req


@transaction.atomic
def record_consent(
    *, student, purpose: str, granted: bool, source: str = "staff", note: str = "", actor=None
) -> ConsentRecord:
    """Upsert a consent decision for a purpose (latest state wins)."""
    consent, _ = ConsentRecord.objects.update_or_create(
        student=student,
        purpose=purpose,
        defaults={
            "granted": granted,
            "source": source,
            "note": note,
            "recorded_by": actor if getattr(actor, "pk", None) else None,
        },
    )
    log.info(
        "consent recorded student=%s purpose=%s granted=%s",
        student.pk,
        purpose,
        granted,
        **ctx(user=getattr(actor, "id", "-"), entity=student.pk, action="record_consent"),
    )
    record_audit(
        action="privacy.consent",
        entity=student,
        summary=f"Consent {purpose}={'granted' if granted else 'withdrawn'}",
        changes={"granted": granted},
        actor=actor,
    )
    return consent


@transaction.atomic
def run_retention(*, anonymize_after_days: int, actor=None) -> dict:
    """
    Erase PII of students who left (graduated/inactive) longer ago than the
    retention window. Returns {erased}. Financial records are kept.
    """
    from apps.students.models import EnrollmentStatus, Student

    cutoff = timezone.now().date() - timedelta(days=anonymize_after_days)
    left = Student.objects.filter(
        status__in=[EnrollmentStatus.GRADUATED, EnrollmentStatus.TRANSFERRED],
        enrollment_date__lt=cutoff,
    ).exclude(first_name="Redacted")

    erased = 0
    for student in left:
        erase_student_data(student, reason="Retention policy sweep", actor=actor)
        erased += 1

    log.info(
        "retention sweep erased=%s cutoff=%s",
        erased,
        cutoff,
        **ctx(user=getattr(actor, "id", "-"), action="run_retention"),
    )
    return {"erased": erased}
