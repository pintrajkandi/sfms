"""
Notification dispatch via Celery.

Email uses Django's mail backend; WhatsApp POSTs to the MSG91 WhatsApp API with
stdlib urllib (no `requests` dependency — mirrors the urllib pattern in
apps/accounts/api.py). Tasks are idempotent, take primitives (ids/strings) not
objects, and set the tenant schema before touching tenant data (CLAUDE.md §5).

PII-safe logging only: phone last-4, never the message body at error, ids and
amounts — never raw personal data (CLAUDE.md §9).
"""

from __future__ import annotations

import json
import urllib.request

from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives

from apps.core.logging import ctx, get_logger

from .messaging import _last4, _normalize_phone, whatsapp_enabled

log = get_logger("notifications.tasks")

# MSG91 WhatsApp send endpoint. Payload is a best-effort placeholder the operator
# tunes to their approved MSG91 template — see .env.example.
MSG91_WHATSAPP_URL = "https://control.msg91.com/api/v5/whatsapp/whatsapp-outbound-message/"

# Each pre-due stage fires exactly once; its cache gate persists well past the
# window so the stage never re-fires. Overdue cadence is read from settings.
_STAGE_TTL = 60 * 60 * 24 * 30  # ~30d — long enough to gate a once-per-stage send


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def send_email(self, to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
    # Domain only — never log the full recipient / body (PII).
    domain = to_email.rsplit("@", 1)[-1] if "@" in to_email else "-"
    log.info(
        "email sending via %s subject=%r to_domain=%s attempt=%s",
        settings.EMAIL_HOST,
        subject,
        domain,
        self.request.retries + 1,
        **ctx(action="send_email"),
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    if html_body:
        message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send()
    except Exception as exc:
        # Loud, structured failure in the worker logs (e.g. MSG91 SMTP rejection).
        log.error(
            "email send FAILED subject=%r to_domain=%s host=%s error=%s",
            subject,
            domain,
            settings.EMAIL_HOST,
            exc,
            **ctx(action="send_email"),
        )
        raise
    log.info(
        "email sent subject=%r to_domain=%s delivered=%s",
        subject,
        domain,
        sent,
        **ctx(action="send_email"),
    )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def send_whatsapp_message(self, to_phone: str, message: str) -> None:
    """
    POST a WhatsApp message to MSG91. Tenant-agnostic once rendered (the caller
    passes a fully-built message), so no schema switch is needed here.

    Guarded: with no creds (dev) we log and return instead of hitting the API.
    """
    phone = _normalize_phone(to_phone)
    if not whatsapp_enabled():
        # Should not normally reach here (send_whatsapp guards too) — belt & braces.
        log.info(
            "whatsapp send skipped: not configured phone=***%s",
            _last4(phone),
            **ctx(action="send_whatsapp_message"),
        )
        return

    log.info(
        "whatsapp sending phone=***%s attempt=%s",
        _last4(phone),
        self.request.retries + 1,
        **ctx(action="send_whatsapp_message"),
    )

    payload = {
        "integrated_number": settings.MSG91_WHATSAPP_NUMBER,
        "content_type": "text",
        "payload": {
            "to": phone,
            "type": "text",
            "text": {"body": message},
        },
    }
    if settings.MSG91_WHATSAPP_NAMESPACE:
        payload["namespace"] = settings.MSG91_WHATSAPP_NAMESPACE

    req = urllib.request.Request(
        MSG91_WHATSAPP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "authkey": settings.MSG91_WHATSAPP_AUTHKEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https host
            status_code = resp.getcode()
    except Exception as exc:
        # No message body at error (may contain PII) — phone last-4 only.
        log.error(
            "whatsapp send FAILED phone=***%s error=%s",
            _last4(phone),
            exc,
            **ctx(action="send_whatsapp_message"),
        )
        raise  # let Celery retry (autoretry_for)

    log.info(
        "whatsapp sent phone=***%s status=%s",
        _last4(phone),
        status_code,
        **ctx(action="send_whatsapp_message"),
    )


@shared_task(bind=True, acks_late=True)
def dispatch_fee_reminders(self) -> None:
    """
    Beat task: sweep every tenant schema and send STAGED, once-per-stage fee
    reminders to guardians. Runs daily (config/celery.py) so each escalation
    stage (T-7 / T-3 / due / overdue) is caught as an invoice reaches it.
    """
    from django_tenants.utils import (
        get_public_schema_name,
        get_tenant_model,
        tenant_context,
    )

    public = get_public_schema_name()
    total_sent = 0
    total_tenants = 0

    for client in get_tenant_model().objects.exclude(schema_name=public):
        total_tenants += 1
        with tenant_context(client):
            total_sent += _remind_tenant()

    log.info(
        "fee reminder sweep done tenants=%s reminders=%s",
        total_tenants,
        total_sent,
        **ctx(action="dispatch_fee_reminders"),
    )


def _stage_message(stage: str, invoice, student) -> str:
    """Escalating, PII-safe reminder body. `stage` is a T-N label or 'overdue'."""
    guardian = student.guardian_name or "Guardian"
    tone = {
        "t7": "is due in a week",
        "t3": "is due in 3 days",
        "t0": "is due today",
        "overdue": "is OVERDUE — please pay immediately to avoid late fees",
    }.get(stage, "is due soon")
    return (
        f"Dear {guardian}, invoice {invoice.invoice_number} for "
        f"{student.full_name} {tone}. Outstanding balance: "
        f"{invoice.balance} {invoice.currency}."
    )


def _send_stage(invoice, student, phone, stage: str) -> None:
    """
    Deliver one staged reminder and log it PII-safe (phone last-4 only).

    Escalation: the urgent stages (due-today, overdue) go out over BOTH WhatsApp
    and SMS; the early nudges (t7, t3) stay WhatsApp-only.
    """
    from .messaging import _last4, _normalize_phone, notify

    urgent = stage in ("t0", "overdue")
    notify(phone, _stage_message(stage, invoice, student), whatsapp=True, sms=urgent)
    log.info(
        "fee reminder queued invoice=%s stage=%s phone=***%s",
        invoice.invoice_number,
        stage,
        _last4(_normalize_phone(phone)),
        **ctx(entity=invoice.pk, action="fee_reminder"),
    )


def _remind_tenant() -> int:
    """
    Staged reminders inside the currently-active tenant schema. Returns count.

    For each unpaid, non-cancelled invoice with a due date, compute days-to-due:
      * before due  — fire each configured T-N stage exactly once (per-stage cache
        gate) when the invoice is within N days of the due date;
      * overdue     — recurring reminder, at most every FEE_REMINDER_OVERDUE_EVERY_DAYS.
    """
    from django.utils import timezone

    from apps.collections.models import Invoice, InvoiceStatus

    days_before = sorted(settings.FEE_REMINDER_DAYS_BEFORE)  # ascending thresholds
    overdue_ttl = settings.FEE_REMINDER_OVERDUE_EVERY_DAYS * 86400

    today = timezone.now().date()
    invoices = (
        Invoice.objects.exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.CANCELLED])
        .filter(due_date__isnull=False)
        .select_related("student")
    )

    sent = 0
    for invoice in invoices:
        student = invoice.student
        phone = getattr(student, "guardian_phone", "")
        if not phone:
            continue

        days_to_due = (invoice.due_date - today).days

        if days_to_due < 0:
            # Overdue — recurring, gated by the overdue cadence.
            key = f"fee_reminder:{invoice.pk}:overdue"
            if cache.get(key):
                continue
            _send_stage(invoice, student, phone, "overdue")
            cache.set(key, 1, overdue_ttl)
            sent += 1
            continue

        # Before due: each N gates independently, fired once as it comes into range.
        for n in days_before:
            if days_to_due > n:
                continue  # not yet within this stage's window
            key = f"fee_reminder:{invoice.pk}:t{n}"
            if cache.get(key):
                continue  # this stage already fired
            _send_stage(invoice, student, phone, f"t{n}")
            cache.set(key, 1, _STAGE_TTL)
            sent += 1

    return sent
