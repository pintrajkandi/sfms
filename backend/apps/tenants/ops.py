"""
Operational health checks for the platform ops panel.

Best-effort pings — every check is wrapped so a dead dependency shows as "down"
rather than 500-ing the page. Never blocks longer than a couple of seconds.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db import connection


def _ok(fn) -> dict:
    try:
        detail = fn()
        return {"ok": True, "detail": detail or "ok"}
    except Exception as exc:  # dependency down
        return {"ok": False, "detail": str(exc)[:120]}


def _db() -> str:
    with connection.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    return "connected"


def _redis() -> str:
    cache.set("ops:ping", "1", 10)
    return "ok" if cache.get("ops:ping") == "1" else "no round-trip"


def _broker() -> str:
    import kombu

    conn = kombu.Connection(settings.CELERY_BROKER_URL)
    conn.ensure_connection(max_retries=1, timeout=2)
    conn.release()
    return "reachable"


def _latest_backup() -> dict:
    from .models import BackupRun

    run = BackupRun.objects.order_by("-created_at").first()
    if run is None:
        return {"ok": False, "detail": "no backups yet"}
    return {
        "ok": run.verified,
        "detail": f"{run.label} · {run.status} · {run.created_at:%Y-%m-%d %H:%M}",
    }


def ops_health() -> list[dict]:
    """Return a list of {name, ok, detail} rows for the panel."""
    rows = [
        {"name": "PostgreSQL", **_ok(_db)},
        {"name": "Redis (cache/sessions)", **_ok(_redis)},
        {"name": "RabbitMQ (Celery broker)", **_ok(_broker)},
        {"name": "Latest backup", **_latest_backup()},
        {
            "name": "MSG91 email",
            "ok": bool(settings.EMAIL_HOST_USER),
            "detail": (
                "configured" if settings.EMAIL_HOST_USER else "not configured (console fallback)"
            ),
        },
        {
            "name": "Razorpay",
            "ok": bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET),
            "detail": "configured" if settings.RAZORPAY_KEY_ID else "not configured",
        },
        {
            "name": "WhatsApp/SMS (MSG91)",
            "ok": bool(settings.MSG91_WHATSAPP_AUTHKEY or settings.MSG91_SMS_AUTHKEY),
            "detail": (
                "configured" if settings.MSG91_WHATSAPP_AUTHKEY else "dev fallback (logs only)"
            ),
        },
        {
            "name": "AI assistant (Claude)",
            "ok": bool(settings.ANTHROPIC_API_KEY),
            "detail": "configured" if settings.ANTHROPIC_API_KEY else "rule-based fallback",
        },
        {
            "name": "Sentry",
            "ok": bool(getattr(settings, "SENTRY_DSN", "")),
            "detail": "configured" if getattr(settings, "SENTRY_DSN", "") else "disabled",
        },
    ]
    return rows
