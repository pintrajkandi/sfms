"""Base models & mixins shared by every tenant app (see CLAUDE.md §5)."""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

# Money is always Decimal + a persisted currency. Never float.
MONEY_MAX_DIGITS = 12
MONEY_DECIMAL_PLACES = 2
ZERO = Decimal("0.00")


def money_field(**kwargs) -> models.DecimalField:
    kwargs.setdefault("max_digits", MONEY_MAX_DIGITS)
    kwargs.setdefault("decimal_places", MONEY_DECIMAL_PLACES)
    kwargs.setdefault("default", ZERO)
    return models.DecimalField(**kwargs)


class Currency(models.TextChoices):
    USD = "USD", "US Dollar"
    EUR = "EUR", "Euro"
    GBP = "GBP", "British Pound"
    INR = "INR", "Indian Rupee"


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to every tenant model."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=True)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(deleted_at__isnull=False)


class SoftDeleteModel(TimeStampedModel):
    """Soft-delete via deleted_at (+ is_active for UI 'archive' toggles)."""

    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self) -> None:
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_active", "deleted_at", "updated_at"])


class MoneyModel(models.Model):
    """Convenience mixin for a single amount + currency pair."""

    amount = money_field()
    currency = models.CharField(
        max_length=3, choices=Currency.choices, default=settings.DEFAULT_CURRENCY
    )

    class Meta:
        abstract = True
