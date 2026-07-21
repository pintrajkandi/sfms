"""
Digital signatures on receipts (CLAUDE.md roadmap — real e-sign, not a static
block).

Each tenant gets an Ed25519 keypair; a payment receipt is signed over a canonical
JSON payload (invoice, student, amount, method, timestamp, IRN if e-invoiced).
The signature + payload hash are stored on the Payment; anyone can verify
authenticity + integrity with the tenant's published public key. Signing is
best-effort at record time — a crypto hiccup must never break a payment write.
"""

from __future__ import annotations

import base64
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from django.utils import timezone

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger

from .models import Payment, SigningKey

log = get_logger("collections.signatures")


def get_active_key() -> SigningKey:
    """The tenant's active signing key, generating one on first use."""
    key = SigningKey.objects.filter(is_active=True).order_by("-created_at").first()
    if key is not None:
        return key
    private = Ed25519PrivateKey.generate()
    public_pem = (
        private.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return SigningKey.objects.create(public_pem=public_pem, private_pem=private_pem)


def rotate_key(*, actor=None) -> SigningKey:
    """Deactivate the current key and mint a new active one."""
    SigningKey.objects.filter(is_active=True).update(is_active=False)
    key = get_active_key()
    record_audit(
        action="signing_key.rotated", entity=key, summary="Signing key rotated", actor=actor
    )
    return key


def canonical_payload(payment: Payment) -> str:
    """Deterministic JSON of the receipt facts that the signature covers."""
    invoice = payment.invoice
    einvoice = getattr(invoice, "einvoice", None)
    payload = {
        "invoice": invoice.invoice_number,
        "student_id": invoice.student.student_id,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "method": payment.method,
        "reference": payment.reference,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else "",
        "irn": getattr(einvoice, "irn", "") if einvoice else "",
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sign_receipt(payment: Payment, *, actor=None) -> Payment:
    """Sign a payment's receipt payload with the active key. Idempotent-ish."""
    key = get_active_key()
    payload = canonical_payload(payment)
    digest = hashlib.sha256(payload.encode()).hexdigest()

    private = serialization.load_pem_private_key(key.private_pem.encode(), password=None)
    signature = private.sign(payload.encode())

    payment.signature = base64.b64encode(signature).decode()
    payment.signed_hash = digest
    payment.signing_key = key
    payment.signed_at = timezone.now()
    payment.save(
        update_fields=["signature", "signed_hash", "signing_key", "signed_at", "updated_at"]
    )

    log.info(
        "receipt signed payment=%s key=%s",
        payment.id,
        key.id,
        **ctx(user=getattr(actor, "id", "-"), entity=payment.id, action="sign_receipt"),
    )
    return payment


def verify_receipt(payment: Payment) -> dict:
    """
    Verify a signed receipt. Returns {signed, valid, reason}. `valid` is True only
    when the stored signature matches a freshly-recomputed payload (tamper-evident).
    """
    if not payment.signature or payment.signing_key is None:
        return {"signed": False, "valid": False, "reason": "not signed"}

    payload = canonical_payload(payment)
    try:
        public: Ed25519PublicKey = serialization.load_pem_public_key(
            payment.signing_key.public_pem.encode()
        )
        public.verify(base64.b64decode(payment.signature), payload.encode())
        return {"signed": True, "valid": True, "reason": "ok"}
    except InvalidSignature:
        return {"signed": True, "valid": False, "reason": "signature mismatch (tampered)"}
    except Exception as exc:  # malformed key/signature
        return {"signed": True, "valid": False, "reason": str(exc)[:120]}
