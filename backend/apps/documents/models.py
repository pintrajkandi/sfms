"""Document store — student docs, receipts, invoices, vendor bills, salary slips."""

from django.db import models

from apps.core.models import TimeStampedModel


class DocumentCategory(models.TextChoices):
    STUDENT = "student", "Student Document"
    RECEIPT = "receipt", "Receipt"
    INVOICE = "invoice", "Invoice"
    VENDOR_BILL = "vendor_bill", "Vendor Bill"
    SALARY_SLIP = "salary_slip", "Salary Slip"
    OTHER = "other", "Other"


class Document(TimeStampedModel):
    title = models.CharField(max_length=200)
    category = models.CharField(
        max_length=20,
        choices=DocumentCategory.choices,
        default=DocumentCategory.OTHER,
        db_index=True,
    )
    file = models.FileField(upload_to="documents/")
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    notes = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.category})"
