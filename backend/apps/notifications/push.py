"""
Web-push delivery (VAPID). Enabled only when VAPID keys are configured; sends are
best-effort and prune dead subscriptions (410/404). Never raises to callers.
"""

from __future__ import annotations

import base64
import json

from django.conf import settings

from apps.core.logging import ctx, get_logger

log = get_logger("notifications.push")


def push_enabled() -> bool:
    return bool(
        getattr(settings, "VAPID_PRIVATE_KEY", "") and getattr(settings, "VAPID_PUBLIC_KEY", "")
    )


def _private_pem() -> str:
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        NoEncryption,
        PrivateFormat,
        load_der_private_key,
    )

    raw = settings.VAPID_PRIVATE_KEY
    der = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
    key = load_der_private_key(der, password=None)
    return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).decode()


def send_web_push(subscription, title: str, body: str, url: str = "/") -> bool:
    """Send one push. Returns True on success; deletes the subscription if gone."""
    if not push_enabled():
        return False
    try:
        from pywebpush import webpush

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=_private_pem(),
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
        return True
    except Exception as exc:  # noqa: BLE001 - never break the caller
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            subscription.delete()
        log.warning(
            "web push failed endpoint=%s status=%s error=%s",
            subscription.endpoint[:40],
            status,
            exc,
            **ctx(action="send_web_push"),
        )
        return False


def push_broadcast(title: str, body: str, url: str = "/") -> int:
    """Push to every subscription in the current tenant. Returns count delivered."""
    from .models import PushSubscription

    sent = 0
    for sub in PushSubscription.objects.all():
        if send_web_push(sub, title, body, url):
            sent += 1
    log.info("push broadcast sent=%s title=%s", sent, title, **ctx(action="push_broadcast"))
    return sent
