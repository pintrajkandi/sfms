"""
Staged fee-reminder escalation (T-7 / T-3 / due / overdue).

Every test runs inside the `test` tenant schema (tenant_ctx) and patches
`send_whatsapp` so nothing leaves the process. The per-stage cache gates are the
mechanism under test, so we clear the cache before each run.
"""

from __future__ import annotations

import datetime

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.notifications import tasks

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    return create_student(first_name="Ada", last_name="Lovelace", **kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def _invoice_due_in(days: int, **student_kw):
    """Create an unpaid invoice whose due_date is `days` from today (may be negative)."""
    from apps.collections.services import create_invoice

    student = _student(
        guardian_name="Grace Hopper",
        guardian_phone="+91 90000 12345",
        **student_kw,
    )
    ft = _fee_type()
    due = timezone.now().date() + datetime.timedelta(days=days)
    return create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": "1000.00"}],
        due_date=due,
    )


@pytest.fixture
def captured(monkeypatch):
    """
    Capture reminder sends and start each test from a clean cache.

    We patch `_send_stage` (the reminder-only delivery seam) rather than the
    shared `send_whatsapp` so that setup-time notices — the invoice-generated
    announcement and payment receipts, which also fan out over WhatsApp — don't
    pollute the counts. The per-stage cache gates live in `_remind_tenant`, so
    they're still exercised. We record the rendered message for assertions.
    """
    cache.clear()
    sends: list[tuple[str, str]] = []

    def fake_send_stage(invoice, student, phone, stage):
        sends.append((phone, tasks._stage_message(stage, invoice, student)))

    monkeypatch.setattr(tasks, "_send_stage", fake_send_stage)
    return sends


# --- per-stage messaging ---------------------------------------------------


def test_t7_stage_fires_at_seven_days(tenant_ctx, captured):
    _invoice_due_in(7)
    tasks._remind_tenant()
    assert len(captured) == 1
    assert "is due in a week" in captured[0][1]


def test_t3_stage_fires_at_three_days(tenant_ctx, captured):
    _invoice_due_in(3)
    tasks._remind_tenant()
    # 3 days out matches BOTH t7 and t3 thresholds — both fire once here.
    tones = [m for _, m in captured]
    assert any("is due in 3 days" in m for m in tones)
    assert any("is due in a week" in m for m in tones)


def test_due_today_stage(tenant_ctx, captured):
    _invoice_due_in(0)
    tasks._remind_tenant()
    tones = [m for _, m in captured]
    assert any("is due today" in m for m in tones)


def test_overdue_stage(tenant_ctx, captured):
    inv = _invoice_due_in(-2)
    tasks._remind_tenant()
    assert len(captured) == 1
    phone, message = captured[0]
    assert "is OVERDUE" in message
    assert inv.invoice_number in message
    assert phone == "+91 90000 12345"


# --- once-per-stage idempotency -------------------------------------------


def test_pre_due_stage_is_once_per_stage(tenant_ctx, captured):
    _invoice_due_in(7)
    tasks._remind_tenant()
    first = len(captured)
    assert first == 1
    tasks._remind_tenant()  # gate holds — no new send for the t7 stage
    assert len(captured) == first


def test_overdue_recurs_only_after_cadence(tenant_ctx, captured, settings):
    settings.FEE_REMINDER_OVERDUE_EVERY_DAYS = 7
    _invoice_due_in(-1)
    tasks._remind_tenant()
    assert len(captured) == 1
    tasks._remind_tenant()  # within the 7-day cadence — gated
    assert len(captured) == 1


# --- exclusions ------------------------------------------------------------


def test_paid_invoice_sends_nothing(tenant_ctx, captured):
    from apps.collections.services import record_payment

    inv = _invoice_due_in(-2)
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="paid-1")
    tasks._remind_tenant()
    assert captured == []


def test_cancelled_invoice_sends_nothing(tenant_ctx, captured):
    from apps.collections.models import InvoiceStatus

    inv = _invoice_due_in(-2)
    inv.status = InvoiceStatus.CANCELLED
    inv.save(update_fields=["status"])
    tasks._remind_tenant()
    assert captured == []


def test_no_guardian_phone_sends_nothing(tenant_ctx, captured):
    from apps.collections.services import create_invoice

    student = _student()  # no guardian_phone
    ft = _fee_type()
    create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": "1000.00"}],
        due_date=timezone.now().date() - datetime.timedelta(days=3),
    )
    tasks._remind_tenant()
    assert captured == []
