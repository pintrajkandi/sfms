"""UPI Autopay / e-mandate lifecycle + auto-debit (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.collections.mandates import (
    activate_mandate,
    cancel_mandate,
    charge_mandate,
    create_mandate,
)
from apps.collections.models import InvoiceStatus, Mandate, MandateCharge
from apps.collections.services import create_invoice
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat = FeeCategory.objects.create(name="Academic")
    return FeeType.objects.create(name="Tuition", category=cat, default_amount="1000.00")


def _invoice(student):
    return create_invoice(
        student=student, lines=[{"fee_type": _fee_type(), "unit_price": "1000.00"}]
    )


def test_create_mandate_mocks_gateway_when_razorpay_disabled(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    settings.RAZORPAY_KEY_SECRET = ""
    m = create_mandate(student=_student(), max_amount="2000.00", currency="INR")
    assert m.status == Mandate.Status.CREATED
    assert m.gateway_ref.startswith("mock_mandate_")
    assert m.auth_url


def test_charge_requires_active_mandate(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="2000.00")
    inv = _invoice(student)
    with pytest.raises(ServiceError):
        charge_mandate(mandate=m, invoice=inv)  # still CREATED, not ACTIVE


def test_activate_then_charge_records_payment(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="2000.00")
    activate_mandate(m)
    inv = _invoice(student)

    charge = charge_mandate(mandate=m, invoice=inv, amount="1000.00")
    assert charge.status == MandateCharge.Status.SUCCEEDED
    assert charge.payment is not None
    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID
    assert inv.amount_paid == Decimal("1000.00")


def test_charge_is_idempotent_per_month(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="2000.00")
    activate_mandate(m)
    inv = _invoice(student)

    c1 = charge_mandate(mandate=m, invoice=inv, amount="1000.00")
    c2 = charge_mandate(mandate=m, invoice=inv, amount="1000.00")
    assert c1.id == c2.id  # same charge, not double-debited
    inv.refresh_from_db()
    assert inv.amount_paid == Decimal("1000.00")


def test_charge_cannot_exceed_max_amount(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="500.00")
    activate_mandate(m)
    inv = _invoice(student)
    with pytest.raises(ServiceError):
        charge_mandate(mandate=m, invoice=inv, amount="1000.00")


def test_cancelled_mandate_cannot_charge(tenant_ctx, settings):
    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="2000.00")
    activate_mandate(m)
    cancel_mandate(m)
    inv = _invoice(student)
    with pytest.raises(ServiceError):
        charge_mandate(mandate=m, invoice=inv, amount="1000.00")


def test_autopay_sweep_charges_due_invoices(tenant_ctx, settings):
    import datetime

    from django.utils import timezone

    from apps.collections.tasks import _autopay_tenant

    settings.RAZORPAY_KEY_ID = ""
    student = _student()
    m = create_mandate(student=student, max_amount="2000.00")
    activate_mandate(m)
    # invoice due yesterday
    inv = create_invoice(
        student=student,
        lines=[{"fee_type": _fee_type(), "unit_price": "800.00"}],
        due_date=timezone.now().date() - datetime.timedelta(days=1),
    )
    charged = _autopay_tenant()
    assert charged == 1
    inv.refresh_from_db()
    assert inv.status == InvoiceStatus.PAID
