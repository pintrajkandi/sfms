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


class AuditLog(models.Model):
    """
    User-facing "who changed what" trail (CLAUDE.md — Audit log). Tenant-scoped
    (this app is in TENANT_APPS), so each school has its own immutable history.

    Written by apps.core.audit.record_audit at the service layer — the same place
    money math and workflow transitions happen — never from a view. `changes` is
    an optional {field: [old, new]} diff; `summary` is the human-readable line.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    actor_label = models.CharField(max_length=200, blank=True)  # snapshot (user may be deleted)
    action = models.CharField(max_length=64, db_index=True)  # e.g. "invoice.created"
    entity_type = models.CharField(max_length=64, blank=True)  # e.g. "Invoice"
    entity_id = models.CharField(max_length=64, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}#{self.entity_id}"
