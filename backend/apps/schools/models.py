"""Per-tenant school settings & academic years (CLAUDE.md — School Settings)."""

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class SchoolSettings(TimeStampedModel):
    """One row per tenant — the school's profile, branding, invoice & contact prefs."""

    class SchoolType(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        CHARTER = "charter", "Charter"
        INTERNATIONAL = "international", "International"

    # --- School Info ---
    name = models.CharField(max_length=200)
    school_type = models.CharField(
        max_length=20, choices=SchoolType.choices, default=SchoolType.PRIVATE
    )
    registration_number = models.CharField(max_length=64, blank=True)
    established_year = models.PositiveIntegerField(null=True, blank=True)
    affiliation_board = models.CharField(max_length=100, blank=True)
    tagline = models.CharField(max_length=200, blank=True)

    # --- Branding & Logos (stored in MinIO) ---
    logo = models.ImageField(upload_to="branding/", null=True, blank=True)
    letterhead_logo = models.ImageField(upload_to="branding/", null=True, blank=True)
    favicon = models.ImageField(upload_to="branding/", null=True, blank=True)
    brand_color = models.CharField(max_length=7, default="#4F46E5")

    # --- Invoice Settings ---
    invoice_prefix = models.CharField(max_length=16, default="INV")
    starting_invoice_number = models.PositiveIntegerField(default=1001)
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=settings.DEFAULT_CURRENCY
    )
    tax_gst_number = models.CharField(max_length=32, blank=True)
    default_tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    payment_due_days = models.PositiveIntegerField(default=30)
    invoice_footer_note = models.TextField(blank=True)
    bank_account_details = models.TextField(blank=True)

    # --- Contact Details ---
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default="India")
    primary_phone = models.CharField(max_length=32, blank=True)
    alternate_phone = models.CharField(max_length=32, blank=True)
    official_email = models.EmailField(blank=True)
    accounts_email = models.EmailField(blank=True)
    website_url = models.URLField(blank=True)
    facebook = models.CharField(max_length=200, blank=True)
    instagram = models.CharField(max_length=200, blank=True)
    linkedin = models.CharField(max_length=200, blank=True)

    # --- Payroll (statutory deduction rates; per-tenant, override the env defaults) ---
    payroll_pf_rate = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.12"))
    payroll_pf_ceiling = money_field(default=Decimal("15000"))
    payroll_esi_rate = models.DecimalField(
        max_digits=6, decimal_places=4, default=Decimal("0.0075")
    )
    payroll_esi_threshold = money_field(default=Decimal("21000"))
    payroll_professional_tax = money_field(default=Decimal("200"))

    # --- Notifications ---
    notify_due_reminders = models.BooleanField(default=True)
    notify_overdue = models.BooleanField(default=True)

    class Meta:
        verbose_name = "School settings"
        verbose_name_plural = "School settings"

    def __str__(self) -> str:
        return self.name


class AcademicYear(TimeStampedModel):
    label = models.CharField(max_length=20, unique=True)  # e.g. "2024-2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ("-start_date",)

    def __str__(self) -> str:
        return self.label


class SchoolClass(TimeStampedModel):
    """A class/grade the admin manages (e.g. "Grade 1", "Class 10"). Feeds the
    student class dropdown; `Student.grade` stores the chosen class name."""

    name = models.CharField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "School classes"
        ordering = ("order", "name")

    def __str__(self) -> str:
        return self.name


class Section(TimeStampedModel):
    """A section within a class (e.g. "A", "B"). Feeds the student section dropdown."""

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("school_class", "name")
        constraints = [
            models.UniqueConstraint(fields=["school_class", "name"], name="uniq_section_class_name")
        ]

    def __str__(self) -> str:
        return f"{self.school_class.name} · {self.name}"


class Department(TimeStampedModel):
    """An admin-managed department (e.g. "Science", "Administration") used to tag
    teachers. Feeds the teacher department dropdown."""

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class SupportTicket(TimeStampedModel):
    """A support request raised by school staff to the platform team."""

    class Category(models.TextChoices):
        BILLING = "billing", "Billing"
        TECHNICAL = "technical", "Technical"
        FEATURE = "feature", "Feature Request"
        ACCOUNT = "account", "Account"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        RESOLVED = "resolved", "Resolved"

    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    message = models.TextField()
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.subject} ({self.status})"
