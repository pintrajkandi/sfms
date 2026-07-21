"""Fee structures: categories, types and per-class/year plans (CLAUDE.md — Fee Structures)."""

from django.db import models

from apps.core.models import Currency, SoftDeleteModel, TimeStampedModel, money_field

# Percentages are stored as a plain Decimal 0–100 (e.g. 12.50 = 12.5%).
PERCENT_MAX_DIGITS = 5
PERCENT_DECIMAL_PLACES = 2


class FeeCategory(TimeStampedModel):
    """Grouping shown on invoices, e.g. Academic, Facility, Extra-Curricular."""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default="#6366F1")

    class Meta:
        verbose_name_plural = "Fee categories"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class FeeType(TimeStampedModel):
    """A billable fee, e.g. Tuition, Lab, Library, Transport, Sports, Exam."""

    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="fee_types")
    default_amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    is_recurring = models.BooleanField(default=True)
    # GST: HSN/SAC classification + rate. Amounts are treated as TAX-INCLUSIVE, so
    # the e-invoice extracts the tax component (education fees are often exempt →
    # leave gst_rate 0). Rate is a percentage 0–28.
    hsn_sac = models.CharField(max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class FeePlan(SoftDeleteModel):
    """
    The amount of a fee type for a given class/grade in an academic year.
    This is what the fee-collection wizard resolves against.
    """

    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT, related_name="plans")
    academic_year = models.ForeignKey(
        "schools.AcademicYear", on_delete=models.PROTECT, related_name="fee_plans"
    )
    grade = models.CharField(max_length=50, blank=True)  # blank = applies to all grades
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fee_type", "academic_year", "grade"],
                name="uniq_feeplan_type_year_grade",
            )
        ]
        ordering = ("academic_year", "grade")

    def __str__(self) -> str:
        return f"{self.fee_type.name} · {self.grade or 'all'} · {self.academic_year}"


class DiscountRule(SoftDeleteModel):
    """
    A reusable concession rule: scholarships, staff-ward discounts, sibling
    discounts, need-/merit-based waivers. Rules are *definitions*; awarding one to
    a student is a StudentDiscount. Sibling rules (auto_apply) resolve from
    enrolment data without an explicit award.

    The amount is computed at invoice time by fees.services.resolve_discounts —
    never stored as a frozen number on the rule.
    """

    class Kind(models.TextChoices):
        SCHOLARSHIP = "scholarship", "Scholarship"
        CONCESSION = "concession", "Concession"
        SIBLING = "sibling", "Sibling discount"
        STAFF_WARD = "staff_ward", "Staff ward"
        MERIT = "merit", "Merit-based"
        NEED_BASED = "need_based", "Need-based"
        OTHER = "other", "Other"

    class Method(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage of amount"
        FIXED = "fixed", "Fixed amount"

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=40, unique=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.CONCESSION)
    method = models.CharField(max_length=12, choices=Method.choices, default=Method.PERCENTAGE)

    # percentage: 0–100; fixed: currency amount. Interpreted per `method`.
    value = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")

    # Optional narrowing: apply only to lines of this fee type (else whole subtotal).
    fee_type = models.ForeignKey(
        FeeType, on_delete=models.PROTECT, null=True, blank=True, related_name="discount_rules"
    )
    # 0 = uncapped. A ceiling on the money any single application can discount.
    max_amount = money_field()

    # Auto rules (e.g. sibling) apply to every eligible student with no award row.
    auto_apply = models.BooleanField(default=False)
    # Non-stackable rules compete; only the single best-value one applies.
    stackable = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=100)  # lower = considered first

    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("priority", "name")

    def __str__(self) -> str:
        unit = "%" if self.method == self.Method.PERCENTAGE else self.currency
        return f"{self.name} ({self.value}{unit})"


class StudentDiscount(TimeStampedModel):
    """Awards a DiscountRule to a specific student (a scholarship grant, etc.)."""

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="discounts"
    )
    rule = models.ForeignKey(DiscountRule, on_delete=models.PROTECT, related_name="awards")
    # Optional per-student override of the rule's value (same units as the rule).
    override_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    awarded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["student", "rule"], name="uniq_student_discount_rule")
        ]

    def __str__(self) -> str:
        return f"{self.rule.name} → {self.student_id}"
