"""Teachers & teacher payouts with an approval workflow (CLAUDE.md — Staff/Teachers)."""

from django.db import models

from apps.core.models import Currency, SoftDeleteModel, TimeStampedModel, money_field


class TeacherStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ON_LEAVE = "on_leave", "On Leave"
    AVAILABLE = "available", "Available"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full-time"
    PART_TIME = "part_time", "Part-time"
    CONTRACT = "contract", "Contract"
    VISITING = "visiting", "Visiting"


class PayFrequency(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    BIWEEKLY = "biweekly", "Bi-weekly"
    WEEKLY = "weekly", "Weekly"
    ANNUAL = "annual", "Annual"


class Teacher(SoftDeleteModel):
    # --- Personal Information ---
    employee_id = models.CharField(max_length=32, unique=True)
    first_name = models.CharField(max_length=100, blank=True)  # API-required (serializer)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to="teachers/", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=TeacherStatus.choices, default=TeacherStatus.ACTIVE
    )

    # --- Professional Details ---
    department = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, blank=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)

    # --- Salary & Increment ---
    base_salary = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    pay_frequency = models.CharField(
        max_length=20, choices=PayFrequency.choices, default=PayFrequency.MONTHLY
    )
    last_increment_date = models.DateField(null=True, blank=True)
    increment_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    next_increment_due = models.DateField(null=True, blank=True)
    increment_reason = models.CharField(max_length=200, blank=True)

    # --- Bank details (no full sensitive data logged — see §9) ---
    bank_name = models.CharField(max_length=120, blank=True)
    account_number = models.CharField(max_length=40, blank=True)
    routing_code = models.CharField(max_length=40, blank=True)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return f"{self.full_name} ({self.employee_id})"


class TeacherClass(TimeStampedModel):
    """A class/subject assignment for a teacher (repeatable rows on the form)."""

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="classes")
    class_name = models.CharField(max_length=100)
    role_in_class = models.CharField(max_length=60, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)

    def __str__(self) -> str:
        return f"{self.class_name} · {self.teacher_id}"


class PayoutStatus(models.TextChoices):
    SUBMITTED = "submitted", "Form Submitted"
    HOD_APPROVED = "hod_approved", "HOD Reviewed"
    FINANCE_APPROVED = "finance_approved", "Finance Reviewed"
    PROCESSED = "processed", "Payment Processed"
    REJECTED = "rejected", "Rejected"


class Payout(TimeStampedModel):
    class PayType(models.TextChoices):
        SALARY = "salary", "Salary"
        BONUS = "bonus", "Bonus"
        REIMBURSEMENT = "reimbursement", "Reimbursement"

    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name="payouts")
    pay_type = models.CharField(max_length=20, choices=PayType.choices, default=PayType.SALARY)
    pay_period = models.CharField(max_length=20)  # e.g. "2024-07"

    base_amount = money_field()
    bonus_amount = money_field()
    deductions = money_field()
    net_amount = money_field()  # computed in services: base + bonus − deductions
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")

    payment_method = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.SUBMITTED,
        db_index=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.teacher.full_name} · {self.pay_period} · {self.status}"


class PayoutApproval(TimeStampedModel):
    """Audit trail of each workflow transition."""

    payout = models.ForeignKey(Payout, on_delete=models.CASCADE, related_name="approvals")
    from_status = models.CharField(max_length=20)
    to_status = models.CharField(max_length=20)
    actor = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
