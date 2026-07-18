"""
Public WhatsApp interface (MSG91) — the module OTHER apps import.

Kept import-light on purpose: the Celery task is imported lazily inside
`send_whatsapp` so importing this module never drags in the worker stack.

Dev fallback: when WhatsApp is not configured (blank creds), messages are logged
(PII-safe) instead of sent — that's how OTPs/receipts are seen locally.

Never log secrets or full PII: phone last-4 + a truncated message only
(CLAUDE.md §9).
"""

from __future__ import annotations

import json
import re
import urllib.request

from celery import shared_task
from django.conf import settings

from apps.core.logging import ctx, get_logger

log = get_logger("notifications.messaging")

# MSG91 SMS send endpoint. Payload is a best-effort placeholder the operator tunes
# to their DLT-approved template — see .env.example.
MSG91_SMS_URL = "https://control.msg91.com/api/v5/flow/"

# How much of a message body we allow into logs (dev fallback only).
_LOG_PREVIEW = 60


def whatsapp_enabled() -> bool:
    """True only when both an auth key and an integrated number are configured."""
    return bool(settings.MSG91_WHATSAPP_AUTHKEY and settings.MSG91_WHATSAPP_NUMBER)


def sms_enabled() -> bool:
    """True only when both an auth key and a DLT sender id are configured."""
    return bool(settings.MSG91_SMS_AUTHKEY and settings.MSG91_SMS_SENDER_ID)


def _normalize_phone(to_phone: str) -> str:
    """Strip everything but digits (MSG91 wants a bare msisdn)."""
    return re.sub(r"\D", "", to_phone or "")


def _last4(phone: str) -> str:
    return phone[-4:] if len(phone) >= 4 else "----"


def send_whatsapp(to_phone: str, message: str) -> None:
    """
    Fire-and-forget WhatsApp send. Never raises — messaging must never break the
    business operation that triggered it.

    - Not configured -> log the message as a DEV FALLBACK and return.
    - Configured     -> enqueue the Celery task (task imported lazily).
    """
    phone = _normalize_phone(to_phone)
    if not phone:
        log.warning("whatsapp skipped: empty phone", **ctx(action="send_whatsapp"))
        return

    if not whatsapp_enabled():
        # DEV FALLBACK — messages print to the worker/app logs, PII-safe.
        log.info(
            "whatsapp DEV FALLBACK (disabled) phone=***%s message=%r",
            _last4(phone),
            message[:_LOG_PREVIEW],
            **ctx(action="send_whatsapp"),
        )
        return

    try:
        from apps.notifications.tasks import send_whatsapp_message

        send_whatsapp_message.delay(phone, message)
    except Exception as exc:  # broker down, import error — never propagate
        log.error(
            "whatsapp enqueue FAILED phone=***%s error=%s",
            _last4(phone),
            exc,
            **ctx(action="send_whatsapp"),
        )


def send_sms(to_phone: str, message: str) -> None:
    """
    Fire-and-forget SMS send. Never raises — messaging must never break the
    business operation that triggered it.

    - Not configured -> log the message as a DEV FALLBACK and return.
    - Configured     -> enqueue the Celery task (task imported lazily).
    """
    phone = _normalize_phone(to_phone)
    if not phone:
        log.warning("sms skipped: empty phone", **ctx(action="send_sms"))
        return

    if not sms_enabled():
        # DEV FALLBACK — messages print to the worker/app logs, PII-safe.
        log.info(
            "sms DEV FALLBACK (disabled) phone=***%s message=%r",
            _last4(phone),
            message[:_LOG_PREVIEW],
            **ctx(action="send_sms"),
        )
        return

    try:
        send_sms_message.delay(phone, message)
    except Exception as exc:  # broker down, import error — never propagate
        log.error(
            "sms enqueue FAILED phone=***%s error=%s",
            _last4(phone),
            exc,
            **ctx(action="send_sms"),
        )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def send_sms_message(self, to_phone: str, message: str) -> None:
    """
    POST an SMS to MSG91. Tenant-agnostic once rendered (the caller passes a
    fully-built message), so no schema switch is needed here.

    Guarded: with no creds (dev) we log and return instead of hitting the API.

    Defined in messaging.py (not tasks.py) but auto-discovered because tasks.py
    imports this module at startup — see the module docstring in tasks.py.
    """
    phone = _normalize_phone(to_phone)
    if not sms_enabled():
        # Should not normally reach here (send_sms guards too) — belt & braces.
        log.info(
            "sms send skipped: not configured phone=***%s",
            _last4(phone),
            **ctx(action="send_sms_message"),
        )
        return

    log.info(
        "sms sending phone=***%s attempt=%s",
        _last4(phone),
        self.request.retries + 1,
        **ctx(action="send_sms_message"),
    )

    # Best-effort payload the operator tunes to their DLT template. The template
    # id + sender are DLT-approved; `message` is passed as a template variable.
    payload = {
        "authkey": settings.MSG91_SMS_AUTHKEY,
        "sender": settings.MSG91_SMS_SENDER_ID,
        "template_id": settings.MSG91_SMS_TEMPLATE_ID,
        "mobiles": phone,
        "message": message,
    }

    req = urllib.request.Request(
        MSG91_SMS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "authkey": settings.MSG91_SMS_AUTHKEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - fixed https host
            status_code = resp.getcode()
    except Exception as exc:
        # No message body at error (may contain PII) — phone last-4 only.
        log.error(
            "sms send FAILED phone=***%s error=%s",
            _last4(phone),
            exc,
            **ctx(action="send_sms_message"),
        )
        raise  # let Celery retry (autoretry_for)

    log.info(
        "sms sent phone=***%s status=%s",
        _last4(phone),
        status_code,
        **ctx(action="send_sms_message"),
    )


def notify(to_phone: str, message: str, *, whatsapp: bool = True, sms: bool = False) -> None:
    """
    Unified fan-out to the enabled channels. Never raises.

    Fans a fully-rendered message out to WhatsApp and/or SMS per the flags. When
    NEITHER channel is enabled we still log the message once (PII-safe) so it's
    visible in dev.
    """
    if whatsapp:
        send_whatsapp(to_phone, message)
    if sms:
        send_sms(to_phone, message)

    wants_channel = (whatsapp and whatsapp_enabled()) or (sms and sms_enabled())
    if not wants_channel:
        # No live channel — surface the message once so dev can read it.
        log.info(
            "notify DEV FALLBACK (no channel enabled) phone=***%s message=%r",
            _last4(_normalize_phone(to_phone)),
            message[:_LOG_PREVIEW],
            **ctx(action="notify"),
        )
