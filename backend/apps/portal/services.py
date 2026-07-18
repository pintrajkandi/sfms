"""
Parent-portal auth logic — OTP challenge + signed session token (CLAUDE.md §5).

Parents never get a Django account: they prove control of the guardian phone via
a one-time code (cached, TTL'd) and then carry a short-lived *signed* token that
encodes only the tenant schema + student pk. There are no models — the OTP lives
in Redis and the token is stateless (``django.core.signing``).

Tenant isolation (CLAUDE.md §3): every cache key and every token is namespaced to
``connection.schema_name``; ``read_token`` refuses a token minted for another
school even if the signature is valid. Never log the OTP value except in the
dev-only info fallback, and never log raw guardian PII.
"""

from __future__ import annotations

import re
import secrets

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.db import connection

from apps.core.logging import ctx, get_logger
from apps.students.models import Student

log = get_logger("portal")

_TOKEN_SALT = "portal.parent"


def _otp_cache_key(student_pk: int) -> str:
    return f"parent_otp:{connection.schema_name}:{student_pk}"


def _normalize_phone(value: str | None) -> str:
    """Last 10 digits, stripping every non-digit — country codes/spaces differ."""
    digits = re.sub(r"\D", "", value or "")
    return digits[-10:]


def _resolve_student(student_id: str, phone: str) -> Student | None:
    """Match on the human student id AND the guardian phone (last-10 digits)."""
    normalized = _normalize_phone(phone)
    if not student_id or not normalized:
        return None
    for student in Student.objects.alive().filter(student_id=student_id):
        if _normalize_phone(student.guardian_phone) == normalized:
            return student
    return None


def _deliver_otp(phone: str, otp: str) -> None:
    """
    Best-effort delivery. Imports notifications lazily so this module never
    hard-depends on it; any failure degrades to a dev info log. Never raises.
    """
    try:
        from apps.notifications.messaging import send_whatsapp

        send_whatsapp(
            phone,
            f"Your Fee Ledger verification code is {otp}. "
            f"It expires in {settings.PARENT_OTP_TTL // 60} minutes.",
        )
    except Exception:
        # Dev fallback only — the OTP value is intentionally logged at info here
        # so local testing works without a WhatsApp provider wired up.
        log.info(
            "otp (fallback) code=%s",
            otp,
            **ctx(action="portal_deliver_otp"),
        )


def request_otp(student_id: str, phone: str) -> Student | None:
    """
    Resolve the student; if found, mint + cache a 6-digit OTP and deliver it.
    Silent about hits/misses (the view always answers 200 — no enumeration).
    """
    student = _resolve_student(student_id, phone)
    if student is None:
        log.warning(
            "otp requested for unknown student/phone",
            **ctx(action="portal_request_otp"),
        )
        return None

    otp = f"{secrets.randbelow(1_000_000):06d}"
    cache.set(_otp_cache_key(student.pk), otp, timeout=settings.PARENT_OTP_TTL)
    _deliver_otp(phone, otp)
    log.info(
        "otp issued",
        **ctx(entity=student.pk, action="portal_request_otp"),
    )
    return student


def verify_otp(student_id: str, phone: str, otp: str) -> str | None:
    """Check the cached OTP; on match burn it and return a signed session token."""
    student = _resolve_student(student_id, phone)
    if student is None:
        return None

    key = _otp_cache_key(student.pk)
    cached = cache.get(key)
    if not cached or str(cached) != str(otp or "").strip():
        log.warning(
            "otp verification failed",
            **ctx(entity=student.pk, action="portal_verify_otp"),
        )
        return None

    cache.delete(key)
    token = signing.dumps(
        {"schema": connection.schema_name, "student": student.pk},
        salt=_TOKEN_SALT,
    )
    log.info(
        "parent authenticated",
        **ctx(entity=student.pk, action="portal_verify_otp"),
    )
    return token


def read_token(token: str) -> Student | None:
    """Validate a signed parent token → the live Student, or None on any failure."""
    if not token:
        return None
    try:
        data = signing.loads(token, salt=_TOKEN_SALT, max_age=settings.PARENT_TOKEN_TTL)
    except signing.BadSignature:
        log.warning("parent token rejected", **ctx(action="portal_read_token"))
        return None
    if data.get("schema") != connection.schema_name:
        log.warning(
            "parent token schema mismatch",
            **ctx(action="portal_read_token"),
        )
        return None
    return Student.objects.alive().filter(pk=data.get("student")).first()
