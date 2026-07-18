"""SMS messaging: enable gate, dev fallback, notify() fan-out, invoice signal."""

import pytest

from apps.notifications import messaging

pytestmark = [pytest.mark.django_db]


def test_sms_disabled_when_unset(settings):
    settings.MSG91_SMS_AUTHKEY = ""
    settings.MSG91_SMS_SENDER_ID = ""
    assert messaging.sms_enabled() is False


def test_sms_enabled_when_both_set(settings):
    settings.MSG91_SMS_AUTHKEY = "key"
    settings.MSG91_SMS_SENDER_ID = "SFMSMS"
    assert messaging.sms_enabled() is True


def test_send_sms_disabled_does_not_raise_or_enqueue(settings, monkeypatch):
    settings.MSG91_SMS_AUTHKEY = ""
    settings.MSG91_SMS_SENDER_ID = ""

    calls = []
    monkeypatch.setattr(
        "apps.notifications.messaging.send_sms_message.delay",
        lambda *a, **k: calls.append((a, k)),
    )

    # Must not raise, and must not enqueue when disabled (dev fallback = log only).
    messaging.send_sms("+91 90000 12345", "hello there")
    assert calls == []


def test_send_sms_enabled_enqueues_normalized_phone(settings, monkeypatch):
    settings.MSG91_SMS_AUTHKEY = "key"
    settings.MSG91_SMS_SENDER_ID = "SFMSMS"

    calls = []
    monkeypatch.setattr(
        "apps.notifications.messaging.send_sms_message.delay",
        lambda *a, **k: calls.append(a),
    )

    messaging.send_sms("+91 90000-12345", "hi")
    assert calls == [("919000012345", "hi")]


def test_notify_fans_out_per_flags(monkeypatch):
    wa, sms = [], []
    monkeypatch.setattr(
        "apps.notifications.messaging.send_whatsapp",
        lambda phone, message: wa.append((phone, message)),
    )
    monkeypatch.setattr(
        "apps.notifications.messaging.send_sms",
        lambda phone, message: sms.append((phone, message)),
    )

    # whatsapp only (default)
    messaging.notify("999", "a")
    assert wa == [("999", "a")]
    assert sms == []

    # both channels
    messaging.notify("999", "b", whatsapp=True, sms=True)
    assert wa == [("999", "a"), ("999", "b")]
    assert sms == [("999", "b")]

    # sms only
    wa.clear()
    sms.clear()
    messaging.notify("999", "c", whatsapp=False, sms=True)
    assert wa == []
    assert sms == [("999", "c")]


def test_notify_no_channel_enabled_still_logs(settings, monkeypatch):
    settings.MSG91_WHATSAPP_AUTHKEY = ""
    settings.MSG91_WHATSAPP_NUMBER = ""
    settings.MSG91_SMS_AUTHKEY = ""
    settings.MSG91_SMS_SENDER_ID = ""

    # Real façades run, but disabled -> dev fallback logs, nothing enqueued.
    wa_delay, sms_delay = [], []
    monkeypatch.setattr(
        "apps.notifications.tasks.send_whatsapp_message.delay",
        lambda *a, **k: wa_delay.append(a),
    )
    monkeypatch.setattr(
        "apps.notifications.messaging.send_sms_message.delay",
        lambda *a, **k: sms_delay.append(a),
    )

    # Must not raise even with both channels off.
    messaging.notify("+91 90000 12345", "hello", whatsapp=True, sms=True)
    assert wa_delay == []
    assert sms_delay == []


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def test_invoice_post_save_triggers_notify(tenant_ctx, monkeypatch):
    from apps.collections.services import create_invoice

    calls = []
    # Patch where the signal looks it up (imported inside the receiver).
    monkeypatch.setattr(
        "apps.notifications.messaging.notify",
        lambda phone, message, **kw: calls.append((phone, message)),
    )

    student = _student(guardian_name="Grace Hopper", guardian_phone="+91 90000 12345")
    ft = _fee_type()
    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])

    assert len(calls) == 1
    phone, message = calls[0]
    assert phone == "+91 90000 12345"
    assert inv.invoice_number in message


def test_invoice_post_save_no_phone_no_notify(tenant_ctx, monkeypatch):
    from apps.collections.services import create_invoice

    calls = []
    monkeypatch.setattr(
        "apps.notifications.messaging.notify",
        lambda phone, message, **kw: calls.append((phone, message)),
    )

    student = _student()  # no guardian_phone
    ft = _fee_type()
    create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])

    assert calls == []
