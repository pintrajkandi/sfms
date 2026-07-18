"""
Thin Razorpay gateway wrapper (CLAUDE.md §5 — external integrations are isolated).

Money is Decimal end-to-end; Razorpay talks in the smallest currency unit
(paise), so amounts are converted at the boundary and nowhere else. All calls
raise ``ServiceError`` when the gateway is not configured so callers can degrade
to a 503. Never log the key secret or webhook secret.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings

from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

log = get_logger("collections.razorpay")


def razorpay_enabled() -> bool:
    """True only when both the key id and secret are configured (read live)."""
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def _client():
    """Build a Razorpay client from settings, or fail loudly if not configured."""
    if not razorpay_enabled():
        raise ServiceError("Online payments not configured.")
    import razorpay

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    return client


def to_paise(amount: Decimal) -> int:
    """Convert a Decimal major-unit amount to an integer number of paise."""
    return int(Decimal(amount) * 100)


def create_order(*, amount: Decimal, receipt: str, notes: dict) -> dict:
    """
    Create a Razorpay order for ``amount`` (major units, Decimal) and return the
    raw order dict. ``notes`` carries the tenant schema + invoice id so the
    webhook can reconcile back to the right school.
    """
    client = _client()
    order = client.order.create(
        {
            "amount": to_paise(amount),
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
            "payment_capture": 1,
        }
    )
    log.info(
        "razorpay order created receipt=%s amount=%s",
        receipt,
        amount,
        **ctx(entity=notes.get("invoice", "-"), action="razorpay_create_order"),
    )
    return order


def verify_payment_signature(params: dict) -> bool:
    """
    Verify a client-side checkout signature (order_id + payment_id + signature).
    Returns True on success; on failure logs a warn and returns False.
    """
    client = _client()
    try:
        client.utility.verify_payment_signature(params)
    except Exception:  # razorpay raises SignatureVerificationError
        log.warning(
            "razorpay payment signature rejected",
            **ctx(action="razorpay_verify_payment"),
        )
        return False
    return True


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Verify a webhook payload against the configured webhook secret. Returns True
    on success; on failure logs a warn and returns False.
    """
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise ServiceError("Razorpay webhook secret not configured.")
    client = _client()
    try:
        client.utility.verify_webhook_signature(
            body.decode("utf-8"),
            signature,
            settings.RAZORPAY_WEBHOOK_SECRET,
        )
    except Exception:
        log.warning(
            "razorpay webhook signature rejected",
            **ctx(action="razorpay_verify_webhook"),
        )
        return False
    return True
