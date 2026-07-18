"""WhatsApp messaging: enable gate, dev fallback, and payment-receipt signal."""

import pytest

from apps.notifications import messaging

pytestmark = [pytest.mark.django_db]


def test_whatsapp_disabled_when_unset(settings):
    settings.MSG91_WHATSAPP_AUTHKEY = ""
    settings.MSG91_WHATSAPP_NUMBER = ""
    assert messaging.whatsapp_enabled() is False


def test_whatsapp_enabled_when_both_set(settings):
    settings.MSG91_WHATSAPP_AUTHKEY = "key"
    settings.MSG91_WHATSAPP_NUMBER = "919999999999"
    assert messaging.whatsapp_enabled() is True


def test_send_whatsapp_disabled_does_not_raise_or_enqueue(settings, monkeypatch):
    settings.MSG91_WHATSAPP_AUTHKEY = ""
    settings.MSG91_WHATSAPP_NUMBER = ""

    calls = []

    def fake_delay(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("apps.notifications.tasks.send_whatsapp_message.delay", fake_delay)

    # Must not raise, and must not enqueue when disabled (dev fallback = log only).
    messaging.send_whatsapp("+91 90000 12345", "hello there")
    assert calls == []


def test_send_whatsapp_enabled_enqueues_normalized_phone(settings, monkeypatch):
    settings.MSG91_WHATSAPP_AUTHKEY = "key"
    settings.MSG91_WHATSAPP_NUMBER = "919999999999"

    calls = []
    monkeypatch.setattr(
        "apps.notifications.tasks.send_whatsapp_message.delay",
        lambda *a, **k: calls.append(a),
    )

    messaging.send_whatsapp("+91 90000-12345", "hi")
    assert calls == [("919000012345", "hi")]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def test_payment_post_save_triggers_whatsapp(tenant_ctx, monkeypatch):
    from apps.collections.services import create_invoice, record_payment

    calls = []
    # Patch where the signal looks it up (imported inside the receiver).
    monkeypatch.setattr(
        "apps.notifications.messaging.send_whatsapp",
        lambda phone, message: calls.append((phone, message)),
    )

    student = _student(guardian_name="Grace Hopper", guardian_phone="+91 90000 12345")
    ft = _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    # Invoice creation itself fires the invoice-generated notice; isolate the
    # receipt under test by discarding that.
    calls.clear()

    record_payment(invoice=inv, amount="400.00", method="cash", idempotency_key="wa1")

    assert len(calls) == 1
    phone, message = calls[0]
    assert phone == "+91 90000 12345"
    assert inv.invoice_number in message


def test_payment_post_save_no_phone_no_send(tenant_ctx, monkeypatch):
    from apps.collections.services import create_invoice, record_payment

    calls = []
    monkeypatch.setattr(
        "apps.notifications.messaging.send_whatsapp",
        lambda phone, message: calls.append((phone, message)),
    )

    student = _student()  # no guardian_phone
    ft = _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    record_payment(invoice=inv, amount="100.00", method="cash", idempotency_key="wa2")

    assert calls == []
