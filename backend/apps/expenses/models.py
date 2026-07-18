"""Expense submissions (CLAUDE.md — Expenses)."""

from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class ExpenseCategory(models.TextChoices):
    SALARIES = "salaries", "Salaries"
    UTILITIES = "utilities", "Utilities"
    MAINTENANCE = "maintenance", "Maintenance"
    SUPPLIES = "supplies", "Supplies"
    TRANSPORT = "transport", "Transport"
    EVENTS = "events", "Events"
    OTHER = "other", "Other"


class Expense(TimeStampedModel):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices)
    expense_date = models.DateField()

    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    payment_method = models.CharField(max_length=32, blank=True)
    reimbursable = models.BooleanField(default=False)

    vendor = models.CharField(max_length=200, blank=True)
    project_cost_center = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    receipt = models.FileField(upload_to="expenses/", null=True, blank=True)

    submitted_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-expense_date",)

    def __str__(self) -> str:
        return f"{self.title} · {self.amount} {self.currency}"
