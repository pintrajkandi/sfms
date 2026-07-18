"""Fee structures: categories, types and per-class/year plans (CLAUDE.md — Fee Structures)."""

from django.db import models

from apps.core.models import Currency, SoftDeleteModel, TimeStampedModel, money_field


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
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    is_recurring = models.BooleanField(default=True)

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
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
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
