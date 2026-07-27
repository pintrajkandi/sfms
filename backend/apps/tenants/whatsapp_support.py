"""WhatsApp verified-support handoff.

A logged-in user requests a support code; we persist it in the PUBLIC schema
(so a platform agent can verify it for any school) and hand back a pre-filled
`wa.me` link. When the customer messages us on WhatsApp with that code, the
agent looks it up in the platform console: a valid, unexpired code proves the
sender is a genuine, signed-in customer.
"""

from __future__ import annotations

import secrets
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.db import connection
from django.utils import timezone
from django_tenants.utils import get_public_schema_name, schema_context

from apps.core.logging import ctx, get_logger

log = get_logger("support.whatsapp")

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no ambiguous 0/O/1/I
CODE_TTL_MINUTES = 30


def _generate_code() -> str:
    return "YC-" + "".join(secrets.choice(_ALPHABET) for _ in range(5))


def _build_url(obj) -> str:
    number = settings.SUPPORT_WHATSAPP_NUMBER
    if not number:
        return ""
    lines = [
        "YukiCares support request",
        f"School: {obj.school_name}" + (f" ({obj.school_code})" if obj.school_code else ""),
        f"Name: {obj.user_name}".rstrip(),
        f"Verification code: {obj.code}",
    ]
    if obj.topic:
        lines.append(f"Issue: {obj.topic}")
    return f"https://wa.me/{number}?text={quote(chr(10).join(lines))}"


def issue_whatsapp_code(*, user, topic: str = "") -> dict:
    """Create a support code for the current tenant + user and return the chat link."""
    from .models import Client, WhatsAppSupportCode

    schema = connection.schema_name
    public = get_public_schema_name()
    if schema == public:
        # Support codes are for school (tenant) users, not the platform console.
        raise ValueError("Support codes can only be issued from a school workspace.")

    with schema_context(public):
        client = Client.objects.filter(schema_name=schema).first()
        school_name = getattr(client, "name", "") or schema
        school_code = getattr(client, "code", "") or ""

        code = _generate_code()
        for _ in range(5):  # retry on the (astronomically unlikely) collision
            if not WhatsAppSupportCode.objects.filter(code=code).exists():
                break
            code = _generate_code()

        obj = WhatsAppSupportCode.objects.create(
            code=code,
            schema_name=schema,
            school_name=school_name,
            school_code=school_code,
            user_name=getattr(user, "full_name", "") or getattr(user, "username", ""),
            user_email=getattr(user, "email", "") or "",
            user_phone=getattr(user, "phone", "") or "",
            topic=(topic or "").strip()[:200],
            expires_at=timezone.now() + timedelta(minutes=CODE_TTL_MINUTES),
        )

    log.info(
        "whatsapp support code issued code=%s",
        obj.code,
        **ctx(user=getattr(user, "id", "-"), entity=obj.code, action="issue_whatsapp_code"),
    )
    return {
        "code": obj.code,
        "expires_at": obj.expires_at.isoformat(),
        "whatsapp_number": settings.SUPPORT_WHATSAPP_NUMBER,
        "whatsapp_url": _build_url(obj),
        "configured": bool(settings.SUPPORT_WHATSAPP_NUMBER),
    }
