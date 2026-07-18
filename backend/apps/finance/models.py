"""Finance ledger — unified income/expense transactions (CLAUDE.md — Finance)."""

from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class EntryType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class LedgerEntry(TimeStampedModel):
    entry_type = models.CharField(max_length=8, choices=EntryType.choices, db_index=True)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    occurred_on = models.DateField(db_index=True)

    # Optional links back to the source document (kept loose to avoid coupling).
    source_type = models.CharField(max_length=40, blank=True)  # e.g. "payment", "expense"
    source_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("-occurred_on", "-created_at")
        indexes = [models.Index(fields=["entry_type", "occurred_on"])]

    def __str__(self) -> str:
        return f"{self.entry_type} {self.amount} {self.currency} · {self.category}"
