"""Signed, self-contained email-verification tokens (no DB table needed)."""
from __future__ import annotations

from django.conf import settings
from django.core import signing

_SALT = "accounts.email-verify"
MAX_AGE_SECONDS = 60 * 60 * 24 * 3  # 3 days


def make_email_token(user_pk: int) -> str:
    return signing.dumps({"uid": user_pk}, salt=_SALT)


def read_email_token(token: str) -> int | None:
    try:
        data = signing.loads(token, salt=_SALT, max_age=MAX_AGE_SECONDS)
        return int(data["uid"])
    except (signing.BadSignature, signing.SignatureExpired, KeyError, ValueError, TypeError):
        return None


def frontend_link(slug: str | None, path: str, **query: str) -> str:
    """Build a link into the tenant's frontend, e.g. /verify-email?token=…"""
    base = f"{slug}.{settings.TENANT_BASE_DOMAIN}" if slug else settings.TENANT_BASE_DOMAIN
    host = f"{base}:{settings.FRONTEND_PORT}" if settings.FRONTEND_PORT else base
    qs = "&".join(f"{k}={v}" for k, v in query.items())
    return f"{settings.FRONTEND_SCHEME}://{host}{path}" + (f"?{qs}" if qs else "")
