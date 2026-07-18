"""
Verification queue — a Celery beat sweep that keeps (re)sending verification
emails to unverified users across every tenant until they verify or the link
expires. Rate-limited per user via the cooldown in services.py, so it never spams
(and it self-heals: once SMTP is fixed, pending users get their email next sweep).
"""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from django_tenants.utils import get_public_schema_name, get_tenant_model, tenant_context

from apps.core.logging import ctx, get_logger

from .tokens import MAX_AGE_SECONDS

log = get_logger("accounts.tasks")


@shared_task(bind=True, acks_late=True)
def dispatch_pending_verifications(self) -> int:
    from .models import User
    from .services import recently_sent, send_verification_email

    cutoff = timezone.now() - timedelta(seconds=MAX_AGE_SECONDS)  # within link validity
    TenantModel = get_tenant_model()
    public = get_public_schema_name()
    sent = 0

    for client in TenantModel.objects.exclude(schema_name=public):
        with tenant_context(client):
            pending = User.objects.filter(email_verified=False, date_joined__gte=cutoff)
            for user in pending:
                if recently_sent(user.pk):  # respect the cooldown
                    continue
                send_verification_email(user, school_name=client.name, slug=client.slug)
                sent += 1

    log.info(
        "verification queue swept dispatched=%s",
        sent,
        **ctx(action="dispatch_pending_verifications"),
    )
    return sent
