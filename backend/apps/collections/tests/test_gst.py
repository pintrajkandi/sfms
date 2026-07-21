"""GST e-invoicing: tax extraction, intra/inter-state split, IRN generation."""

import json
from decimal import Decimal

import pytest

from apps.collections.gst import compute_gst, einvoice_enabled, generate_einvoice
from apps.collections.models import EInvoice
from apps.collections.services import create_invoice
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def _school(state="Karnataka", gstin="29ABCDE1234F1Z5"):
    from apps.schools.models import SchoolSettings

    SchoolSettings.objects.all().delete()
    return SchoolSettings.objects.create(
        name="Demo School", state_province=state, tax_gst_number=gstin
    )


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type(name="Transport", amount="1000.00", gst_rate="18.00", hsn="9966"):
    from apps.fees.models import FeeCategory, FeeType

    cat, _ = FeeCategory.objects.get_or_create(name="Facility")
    return FeeType.objects.create(
        name=name, category=cat, default_amount=amount, gst_rate=gst_rate, hsn_sac=hsn
    )


def test_disabled_without_credentials(settings):
    settings.GST_EINVOICE_BASE_URL = ""
    assert einvoice_enabled() is False


def test_tax_extracted_from_inclusive_amount_intra_state(tenant_ctx):
    _school(state="Karnataka")
    ft = _fee_type(gst_rate="18.00")
    inv = create_invoice(student=_student(), lines=[{"fee_type": ft, "unit_price": "1180.00"}])
    # place_of_supply blank -> intra-state (same as school) -> CGST+SGST
    breakup = compute_gst(inv)
    assert breakup["taxable_value"] == Decimal("1000.00")  # 1180 incl 18% -> 1000 base
    assert breakup["total_tax"] == Decimal("180.00")
    assert breakup["cgst"] == Decimal("90.00")
    assert breakup["sgst"] == Decimal("90.00")
    assert breakup["igst"] == Decimal("0.00")


def test_inter_state_uses_igst(tenant_ctx):
    _school(state="Karnataka")
    ft = _fee_type(gst_rate="18.00")
    inv = create_invoice(student=_student(), lines=[{"fee_type": ft, "unit_price": "1180.00"}])
    inv.place_of_supply = "Maharashtra"
    inv.save(update_fields=["place_of_supply"])
    breakup = compute_gst(inv)
    assert breakup["igst"] == Decimal("180.00")
    assert breakup["cgst"] == Decimal("0.00")


def test_exempt_fee_has_zero_tax(tenant_ctx):
    _school()
    ft = _fee_type(name="Tuition", gst_rate="0")
    inv = create_invoice(student=_student(), lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    breakup = compute_gst(inv)
    assert breakup["total_tax"] == Decimal("0.00")
    assert breakup["taxable_value"] == Decimal("1000.00")


def test_generate_einvoice_mock_irn_and_idempotent(tenant_ctx, settings):
    settings.GST_EINVOICE_BASE_URL = ""  # force mock path
    _school()
    ft = _fee_type(gst_rate="18.00")
    inv = create_invoice(student=_student(), lines=[{"fee_type": ft, "unit_price": "1180.00"}])

    ei = generate_einvoice(inv)
    assert ei.status == EInvoice.Status.GENERATED
    assert len(ei.irn) == 64  # sha256 hex
    assert ei.total_tax == Decimal("180.00")
    qr = json.loads(ei.signed_qr)
    assert qr["DocNo"] == inv.invoice_number
    assert qr["Irn"] == ei.irn

    again = generate_einvoice(inv)
    assert again.id == ei.id  # idempotent — same row
    assert EInvoice.objects.filter(invoice=inv).count() == 1


def test_generate_requires_gstin(tenant_ctx, settings):
    settings.GST_EINVOICE_BASE_URL = ""
    settings.GST_EINVOICE_GSTIN = ""
    _school(gstin="")  # no school GSTIN either
    ft = _fee_type()
    inv = create_invoice(student=_student(), lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    with pytest.raises(ServiceError):
        generate_einvoice(inv)
