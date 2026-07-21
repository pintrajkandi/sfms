"""Finance ledger — unified income/expense transactions (CLAUDE.md — Finance)."""

from django.db import models
from django.db.models import Q

from apps.core.models import Currency, TimeStampedModel, money_field


class EntryType(models.TextChoices):
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


# --------------------------------------------------------------------------- #
# Double-entry accounting: Chart of Accounts + Journal (each entry balances).
# --------------------------------------------------------------------------- #
class AccountType(models.TextChoices):
    ASSET = "asset", "Asset"
    LIABILITY = "liability", "Liability"
    EQUITY = "equity", "Equity"
    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


# Types whose balance grows on the debit side (assets, expenses); the rest grow
# on the credit side (liabilities, equity, income).
DEBIT_NORMAL = {AccountType.ASSET, AccountType.EXPENSE}


class Account(TimeStampedModel):
    """A chart-of-accounts head. `is_system` accounts are seeded and protected."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=12, choices=AccountType.choices, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class JournalEntry(TimeStampedModel):
    """A balanced set of debit/credit lines. Total debits must equal total credits."""

    date = models.DateField(db_index=True)
    narration = models.CharField(max_length=255, blank=True)
    # Optional link back to the document that generated this entry (idempotency).
    source_type = models.CharField(max_length=40, blank=True)  # payment / expense / …
    source_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("-date", "-created_at")
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"],
                condition=Q(source_id__isnull=False),
                name="uniq_journal_source",
            )
        ]

    def __str__(self) -> str:
        return f"Journal #{self.pk} {self.date} {self.narration}"


class JournalLine(TimeStampedModel):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="lines")
    debit = money_field()
    credit = money_field()
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.account.code} Dr {self.debit} Cr {self.credit}"


class LedgerEntry(TimeStampedModel):
    entry_type = models.CharField(max_length=8, choices=EntryType.choices, db_index=True)
    category = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    occurred_on = models.DateField(db_index=True)

    # Optional links back to the source document (kept loose to avoid coupling).
    source_type = models.CharField(max_length=40, blank=True)  # e.g. "payment", "expense"
    source_id = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("-occurred_on", "-created_at")
        indexes = [models.Index(fields=["entry_type", "occurred_on"])]

    def __str__(self) -> str:
        return f"{self.entry_type} {self.amount} {self.currency} · {self.category}"
