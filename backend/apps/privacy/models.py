"""
Data-privacy models (DPDP / FERPA / GDPR) — consent + data-subject requests.

Tenant-scoped: each school owns its consent ledger and request history. The
actual export/erasure logic lives in apps.privacy.services (business logic in
services — CLAUDE.md §5).
"""

from django.db import models

from apps.core.models import TimeStampedModel


class ConsentRecord(TimeStampedModel):
    """A subject's consent for a specific processing purpose (latest state)."""

    class Purpose(models.TextChoices):
        DATA_PROCESSING = "data_processing", "Core data processing"
        MARKETING = "marketing", "Marketing / newsletters"
        PHOTO_USAGE = "photo_usage", "Photo & media usage"
        THIRD_PARTY = "third_party", "Third-party sharing"

    class Source(models.TextChoices):
        ENROLMENT = "enrolment", "Enrolment form"
        PORTAL = "portal", "Parent portal"
        IMPORT = "import", "Bulk import"
        STAFF = "staff", "Recorded by staff"

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="consents"
    )
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    granted = models.BooleanField(default=False)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.STAFF)
    note = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["student", "purpose"], name="uniq_consent_student_purpose"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_purpose_display()}={'yes' if self.granted else 'no'} ({self.student_id})"


class DataSubjectRequest(TimeStampedModel):
    """
    A GDPR/DPDP data-subject request (access/export, erasure, rectification) and
    its outcome. The student FK is kept even after erasure (the row is anonymized
    in place, not deleted, to preserve financial audit integrity).
    """

    class Kind(models.TextChoices):
        ACCESS = "access", "Access / export"
        ERASURE = "erasure", "Erasure"
        RECTIFICATION = "rectification", "Rectification"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="privacy_requests",
    )
    subject_label = models.CharField(max_length=200)  # snapshot (survives erasure)
    kind = models.CharField(max_length=14, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    summary = models.CharField(max_length=255, blank=True)
    requested_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.get_kind_display()} · {self.subject_label} [{self.status}]"
