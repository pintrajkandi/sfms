"""
Parent-portal auth + fee endpoints (CLAUDE.md §8). Nothing external is hit:
``_deliver_otp`` is patched to capture the code and the Razorpay gateway is
patched/left disabled. Every test runs inside the ``test`` tenant schema.
"""

from __future__ import annotations

import pytest
from django.core.cache import cache
from django.db import connection
from rest_framework.test import APIRequestFactory

from apps.portal import services
from apps.portal.services import read_token
from apps.portal.views import PortalFeesView, PortalPayOrderView

pytestmark = [pytest.mark.django_db]

factory = APIRequestFactory()


def _student(student_id="STU-1", phone="+91 98765 43210"):
    from apps.students.services import create_student

    return create_student(
        student_id=student_id,
        first_name="Ada",
        last_name="Lovelace",
        guardian_name="Byron",
        guardian_phone=phone,
    )


def _capture_otp(monkeypatch):
    """Patch delivery to capture the OTP instead of sending it."""
    captured: dict[str, str] = {}

    def fake_deliver(phone, otp):
        captured["phone"] = phone
        captured["otp"] = otp

    monkeypatch.setattr(services, "_deliver_otp", fake_deliver)
    return captured


# --------------------------------------------------------------------------- #
# OTP request → verify → token → read_token happy path.
# --------------------------------------------------------------------------- #
def test_request_and_verify_otp_happy_path(tenant_ctx, monkeypatch):
    student = _student()
    captured = _capture_otp(monkeypatch)

    # A different country-code formatting still matches on last-10 digits.
    services.request_otp("STU-1", "9876543210")
    assert captured["otp"]
    # OTP is cached under the tenant-scoped key.
    assert cache.get(f"parent_otp:{connection.schema_name}:{student.pk}") == captured["otp"]

    token = services.verify_otp("STU-1", "9876543210", captured["otp"])
    assert token
    # OTP is single-use — burned on verify.
    assert cache.get(f"parent_otp:{connection.schema_name}:{student.pk}") is None

    resolved = read_token(token)
    assert resolved is not None
    assert resolved.pk == student.pk


def test_wrong_otp_returns_none(tenant_ctx, monkeypatch):
    _student()
    captured = _capture_otp(monkeypatch)
    services.request_otp("STU-1", "9876543210")
    assert captured["otp"]

    assert services.verify_otp("STU-1", "9876543210", "000000") is None


def test_request_otp_unknown_student_is_silent(tenant_ctx, monkeypatch):
    _student()
    captured = _capture_otp(monkeypatch)
    # Right student id, wrong phone → no OTP delivered, no raise.
    assert services.request_otp("STU-1", "1111111111") is None
    assert captured == {}


# --------------------------------------------------------------------------- #
# Fee endpoint: token gates access.
# --------------------------------------------------------------------------- #
def test_fees_with_valid_token(tenant_ctx, monkeypatch):
    student = _student()
    captured = _capture_otp(monkeypatch)
    services.request_otp("STU-1", "9876543210")
    token = services.verify_otp("STU-1", "9876543210", captured["otp"])

    request = factory.get("/api/v1/portal/fees/", HTTP_X_PARENT_TOKEN=token)
    response = PortalFeesView.as_view()(request)
    assert response.status_code == 200
    assert "total_fee" in response.data
    assert response.data["total_fee"] == "0.00"
    assert student.pk  # sanity


def test_fees_without_token_is_401(tenant_ctx):
    _student()
    request = factory.get("/api/v1/portal/fees/")
    response = PortalFeesView.as_view()(request)
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# Pay order degrades to 503 when Razorpay is not configured.
# --------------------------------------------------------------------------- #
def test_pay_order_503_when_razorpay_disabled(tenant_ctx, settings, monkeypatch):
    settings.RAZORPAY_KEY_ID = ""
    settings.RAZORPAY_KEY_SECRET = ""
    from apps.collections.services import create_invoice
    from apps.fees.models import FeeCategory, FeeType

    student = _student()
    captured = _capture_otp(monkeypatch)
    services.request_otp("STU-1", "9876543210")
    token = services.verify_otp("STU-1", "9876543210", captured["otp"])

    cat = FeeCategory.objects.create(name="Academic")
    ft = FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")
    invoice = create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": "1000.00"}],
        currency="INR",
    )

    request = factory.post(
        "/api/v1/portal/pay/order/",
        {"invoice": invoice.id},
        format="json",
        HTTP_X_PARENT_TOKEN=token,
    )
    response = PortalPayOrderView.as_view()(request)
    assert response.status_code == 503
    assert response.data["detail"] == "Online payments not configured."
