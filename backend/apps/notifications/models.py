"""Web-push subscriptions (browser Push API endpoints per staff user)."""

from django.db import models

from apps.core.models import TimeStampedModel


class PushSubscription(TimeStampedModel):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"push://{self.endpoint[:40]}…"
