"""
Razorpay gateway integration — config gating, client-side verify, and
idempotent reconciliation (CLAUDE.md §8). The razorpay library is never hit:
gateway functions are patched so no network call is made.
"""

from decimal import Decimal

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.collections import gateway
from apps.collections.models import InvoiceStatus, Payment
from apps.collections.services import create_invoice
from apps.collections.views import (
    RazorpayConfigView,
    RazorpayOrderView,
    RazorpayVerifyView,
)

pytestmark = [pytest.mark.django_db]

factory = APIRequestFactory()


def _user():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(username="staff", email="staff@test.local", password="x")


def _invoice(amount="1000.00"):
    from apps.fees.models import FeeCategory, FeeType
    from apps.students.services import create_student

    student = create_student(first_name="Ada", last_name="Lovelace")
    cat = FeeCategory.objects.create(name="Academic")
    ft = FeeType.objects.create(name="Tuition", category=cat, default_amount=amount)
    return create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": amount}],
        currency="INR",
    )


# --------------------------------------------------------------------------- #
# (a) disabled by default: config → enabled False; order → 503.
# --------------------------------------------------------------------------- #
def test_config_reports_disabled_when_unset(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    settings.RAZORPAY_KEY_SECRET = ""
    request = factory.get("/api/v1/payments/razorpay/config/")
    response = RazorpayConfigView.as_view()(request)
    assert response.status_code == 200
    assert response.data == {"enabled": False, "key_id": ""}


def test_order_returns_503_when_unset(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    settings.RAZORPAY_KEY_SECRET = ""
    inv = _invoice()
    user = _user()
    request = factory.post("/api/v1/payments/razorpay/order/", {"invoice": inv.id}, format="json")
    force_authenticate(request, user=user)
    response = RazorpayOrderView.as_view()(request)
    assert response.status_code == 503
    assert response.data["detail"] == "Online payments not configured."


# --------------------------------------------------------------------------- #
# (b) enabled + mocked signature verify: order creates, verify records a
#     payment and moves the invoice toward paid.
# --------------------------------------------------------------------------- #
def _enable(settings):
    settings.RAZORPAY_KEY_ID = "rzp_test_key"
    settings.RAZORPAY_KEY_SECRET = "secret"
    settings.RAZORPAY_WEBHOOK_SECRET = "whsecret"


def test_order_then_verify_records_payment(tenant_ctx, settings, monkeypatch):
    _enable(settings)
    inv = _invoice("1000.00")
    user = _user()

    captured = {}

    def fake_create_order(*, amount, receipt, notes):
        captured["amount"] = amount
        captured["notes"] = notes
        return {"id": "order_1", "amount": gateway.to_paise(amount)}

    monkeypatch.setattr(gateway, "create_order", fake_create_order)

    req = factory.post("/api/v1/payments/razorpay/order/", {"invoice": inv.id}, format="json")
    force_authenticate(req, user=user)
    resp = RazorpayOrderView.as_view()(req)
    assert resp.status_code == 200
    assert resp.data["order_id"] == "order_1"
    assert resp.data["amount"] == 100000  # 1000.00 in paise
    assert resp.data["currency"] == "INR"
    assert captured["amount"] == Decimal("1000.00")
    assert captured["notes"]["schema"] == "test"
    assert captured["notes"]["invoice"] == inv.id

    monkeypatch.setattr(gateway, "verify_payment_signature", lambda params: True)
    req2 = factory.post(
        "/api/v1/payments/razorpay/verify/",
        {
            "invoice": inv.id,
            "razorpay_order_id": "order_1",
            "razorpay_payment_id": "pay_1",
            "razorpay_signature": "sig",
        },
        format="json",
    )
    force_authenticate(req2, user=user)
    resp2 = RazorpayVerifyView.as_view()(req2)
    assert resp2.status_code == 200
    assert resp2.data["status"] == "recorded"

    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID
    assert inv.amount_paid == Decimal("1000.00")
    payment = Payment.objects.get(idempotency_key="pay_1")
    assert payment.method == "razorpay"
    assert payment.reference == "pay_1"


def test_verify_rejects_bad_signature(tenant_ctx, settings, monkeypatch):
    _enable(settings)
    inv = _invoice("500.00")
    user = _user()
    monkeypatch.setattr(gateway, "verify_payment_signature", lambda params: False)
    req = factory.post(
        "/api/v1/payments/razorpay/verify/",
        {
            "invoice": inv.id,
            "razorpay_order_id": "order_1",
            "razorpay_payment_id": "pay_bad",
            "razorpay_signature": "nope",
        },
        format="json",
    )
    force_authenticate(req, user=user)
    resp = RazorpayVerifyView.as_view()(req)
    assert resp.status_code == 400
    assert not Payment.objects.filter(idempotency_key="pay_bad").exists()


# --------------------------------------------------------------------------- #
# (c) idempotency: verifying the same razorpay_payment_id twice (client-verify
#     then webhook, or a double-submit) yields exactly ONE payment.
# --------------------------------------------------------------------------- #
def test_same_payment_id_twice_is_idempotent(tenant_ctx, settings, monkeypatch):
    _enable(settings)
    inv = _invoice("800.00")
    user = _user()
    monkeypatch.setattr(gateway, "verify_payment_signature", lambda params: True)

    def _verify():
        req = factory.post(
            "/api/v1/payments/razorpay/verify/",
            {
                "invoice": inv.id,
                "razorpay_order_id": "order_x",
                "razorpay_payment_id": "pay_dup",
                "razorpay_signature": "sig",
            },
            format="json",
        )
        force_authenticate(req, user=user)
        return RazorpayVerifyView.as_view()(req)

    r1 = _verify()
    r2 = _verify()
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert Payment.objects.filter(idempotency_key="pay_dup").count() == 1
    inv.refresh_from_db()
    assert inv.amount_paid == Decimal("800.00")  # credited once, not twice
