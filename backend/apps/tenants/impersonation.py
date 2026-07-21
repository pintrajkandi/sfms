"""
Secure, time-boxed impersonation ("log in as school admin") for support.

The platform operator mints a signed ticket (SECRET_KEY-signed, so only the
platform can create one; scoped to a single schema; ~2 min TTL). The tenant-side
/auth/impersonate/ endpoint validates it and establishes a session as the target
user — every start is written to the tenant's audit log.
"""

from __future__ import annotations

from django.conf import settings
from django.core import signing

_SALT = "sfms.impersonation"
DEFAULT_TTL = 120  # seconds


def make_ticket(*, operator, target_user_id: int, schema: str) -> str:
    return signing.dumps(
        {
            "op": getattr(operator, "pk", None),
            "op_email": getattr(operator, "email", "") or getattr(operator, "username", ""),
            "uid": target_user_id,
            "schema": schema,
        },
        salt=_SALT,
    )


def read_ticket(token: str, *, max_age: int = DEFAULT_TTL) -> dict:
    """Raises signing.BadSignature / SignatureExpired on invalid/expired tickets."""
    return signing.loads(token, salt=_SALT, max_age=max_age)


def impersonation_url(*, slug: str, ticket: str) -> str:
    base = getattr(settings, "TENANT_BASE_DOMAIN", "localhost")
    scheme = getattr(settings, "FRONTEND_SCHEME", "http")
    port = getattr(settings, "FRONTEND_PORT", "5173")
    return f"{scheme}://{slug}.{base}:{port}/impersonate?ticket={ticket}"
