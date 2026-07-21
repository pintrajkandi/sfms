"""Digital signatures on receipts (Ed25519) — CLAUDE.md §8."""

from decimal import Decimal

import pytest

from apps.collections.models import SigningKey
from apps.collections.services import create_invoice, record_payment
from apps.collections.signatures import get_active_key, rotate_key, verify_receipt

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat, _ = FeeCategory.objects.get_or_create(name="Academic")
    ft, _ = FeeType.objects.get_or_create(
        name="Tuition", defaults={"category": cat, "default_amount": "1000.00"}
    )
    return ft


def _payment(idem="s1"):
    inv = create_invoice(
        student=_student(), lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )
    return record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key=idem)


def test_active_key_generated_once(tenant_ctx):
    k1 = get_active_key()
    k2 = get_active_key()
    assert k1.id == k2.id
    assert k1.algorithm == "ed25519"
    assert "PUBLIC KEY" in k1.public_pem


def test_payment_is_auto_signed(tenant_ctx):
    payment = _payment("auto-sign")
    assert payment.signature
    assert payment.signed_hash
    assert payment.signing_key is not None
    assert payment.signed_at is not None


def test_verify_valid_signature(tenant_ctx):
    payment = _payment("verify-ok")
    result = verify_receipt(payment)
    assert result == {"signed": True, "valid": True, "reason": "ok"}


def test_tampered_receipt_fails_verification(tenant_ctx):
    payment = _payment("tamper")
    # Mutate the covered amount WITHOUT re-signing → signature no longer matches.
    payment.amount = Decimal("9999.00")
    payment.save(update_fields=["amount"])
    result = verify_receipt(payment)
    assert result["signed"] is True
    assert result["valid"] is False
    assert "mismatch" in result["reason"]


def test_unsigned_payment_reports_not_signed(tenant_ctx):
    payment = _payment("unsigned")
    payment.signature = ""
    payment.signing_key = None
    payment.save(update_fields=["signature", "signing_key"])
    result = verify_receipt(payment)
    assert result == {"signed": False, "valid": False, "reason": "not signed"}


def test_rotate_key_activates_new_and_keeps_old(tenant_ctx):
    old = get_active_key()
    new = rotate_key()
    assert new.id != old.id
    old.refresh_from_db()
    assert old.is_active is False
    assert new.is_active is True
    assert SigningKey.objects.count() == 2


def test_signature_reverifies_after_rotation(tenant_ctx):
    # A receipt signed with the old key still verifies against its own key.
    payment = _payment("pre-rotate")
    rotate_key()
    assert verify_receipt(payment)["valid"] is True
