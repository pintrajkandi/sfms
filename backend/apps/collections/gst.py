"""
GST e-invoicing (IRN + signed QR) — CLAUDE.md roadmap.

Fee amounts are treated as TAX-INCLUSIVE, so we *extract* the GST component per
line from its fee type's `gst_rate` (education fees are usually exempt, rate 0).
Intra-state supply → CGST + SGST; inter-state → IGST. The IRN/QR come from the
Invoice Registration Portal (IRP); when creds are unset we produce a
deterministic mock so the flow is testable in dev — same env-gate pattern as the
Razorpay gateway.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import ServiceError

from .models import EInvoice, Invoice, InvoiceStatus

log = get_logger("collections.gst")

_CENTS = Decimal("0.01")
_HUNDRED = Decimal("100")


def einvoice_enabled() -> bool:
    """Live IRP registration requires a base URL + API credentials."""
    return bool(
        settings.GST_EINVOICE_BASE_URL
        and settings.GST_EINVOICE_API_USER
        and settings.GST_EINVOICE_API_PASSWORD
    )


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_CENTS)


def _supplier_state() -> str:
    """Supplier state — env override, else the tenant's SchoolSettings state."""
    if settings.GST_SUPPLIER_STATE:
        return settings.GST_SUPPLIER_STATE
    from apps.schools.models import SchoolSettings

    return (SchoolSettings.objects.values_list("state_province", flat=True).first() or "").strip()


def _supplier_gstin() -> str:
    if settings.GST_EINVOICE_GSTIN:
        return settings.GST_EINVOICE_GSTIN
    from apps.schools.models import SchoolSettings

    return (SchoolSettings.objects.values_list("tax_gst_number", flat=True).first() or "").strip()


def _extract_tax(inclusive_amount: Decimal, rate: Decimal) -> tuple[Decimal, Decimal]:
    """From a tax-inclusive amount, return (taxable_value, tax_amount)."""
    inclusive_amount = Decimal(inclusive_amount)
    rate = Decimal(rate or 0)
    if rate <= ZERO:
        return _q(inclusive_amount), ZERO
    taxable = inclusive_amount * _HUNDRED / (_HUNDRED + rate)
    return _q(taxable), _q(inclusive_amount - taxable)


def compute_gst(invoice: Invoice) -> dict:
    """
    Extract the GST breakup for an invoice from its tax-inclusive lines.
    Returns taxable_value, cgst, sgst, igst, total_tax and per-line items.
    """
    supplier_state = _supplier_state().lower()
    buyer_state = (invoice.place_of_supply or supplier_state).lower()
    intra_state = buyer_state == supplier_state

    taxable_total = cgst = sgst = igst = ZERO
    items = []
    for line in invoice.lines.select_related("fee_type").all():
        rate = Decimal(getattr(line.fee_type, "gst_rate", 0) or 0)
        taxable, tax = _extract_tax(line.amount, rate)
        if intra_state:
            half = _q(tax / 2)
            line_cgst, line_sgst, line_igst = half, _q(tax - half), ZERO
        else:
            line_cgst, line_sgst, line_igst = ZERO, ZERO, tax
        taxable_total += taxable
        cgst += line_cgst
        sgst += line_sgst
        igst += line_igst
        items.append(
            {
                "hsn_sac": getattr(line.fee_type, "hsn_sac", "") or "",
                "description": line.description or line.fee_type.name,
                "quantity": line.quantity,
                "gst_rate": str(rate),
                "taxable_value": str(taxable),
                "cgst": str(line_cgst),
                "sgst": str(line_sgst),
                "igst": str(line_igst),
                "total": str(line.amount),
            }
        )
    return {
        "taxable_value": _q(taxable_total),
        "cgst": _q(cgst),
        "sgst": _q(sgst),
        "igst": _q(igst),
        "total_tax": _q(cgst + sgst + igst),
        "intra_state": intra_state,
        "items": items,
    }


def build_payload(invoice: Invoice, breakup: dict) -> dict:
    """Assemble the IRP e-invoice document (simplified NIC schema)."""
    student = invoice.student
    return {
        "Version": "1.1",
        "TranDtls": {"TaxSch": "GST", "SupTyp": "B2C"},
        "DocDtls": {
            "Typ": "INV",
            "No": invoice.invoice_number,
            "Dt": invoice.issue_date.strftime("%d/%m/%Y"),
        },
        "SellerDtls": {
            "Gstin": _supplier_gstin(),
            "Stcd": _supplier_state(),
        },
        "BuyerDtls": {
            "Nm": student.full_name,
            "Pos": invoice.place_of_supply or _supplier_state(),
        },
        "ItemList": breakup["items"],
        "ValDtls": {
            "AssVal": str(breakup["taxable_value"]),
            "CgstVal": str(breakup["cgst"]),
            "SgstVal": str(breakup["sgst"]),
            "IgstVal": str(breakup["igst"]),
            "TotInvVal": str(invoice.total),
        },
    }


def _mock_registration(invoice: Invoice, payload: dict) -> dict:
    """Deterministic IRN + QR when the IRP is not configured (dev fallback)."""
    fy = invoice.issue_date.strftime("%Y")
    seed = f"{_supplier_gstin()}|{invoice.invoice_number}|{fy}".encode()
    irn = hashlib.sha256(seed).hexdigest()
    qr = json.dumps(
        {
            "SellerGstin": _supplier_gstin(),
            "DocNo": invoice.invoice_number,
            "DocDt": payload["DocDtls"]["Dt"],
            "TotInvVal": str(invoice.total),
            "Irn": irn,
            "IrnDt": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    return {
        "irn": irn,
        "ack_no": irn[:16].upper(),
        "ack_date": timezone.now(),
        "signed_qr": qr,
    }


def _register_with_irp(payload: dict) -> dict:  # pragma: no cover - network path
    """Call the real IRP. Kept thin; raises ServiceError on any failure."""
    import requests

    try:
        resp = requests.post(
            f"{settings.GST_EINVOICE_BASE_URL.rstrip('/')}/invoice",
            json=payload,
            auth=(settings.GST_EINVOICE_API_USER, settings.GST_EINVOICE_API_PASSWORD),
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise ServiceError(f"IRP registration failed: {exc}") from exc
    return {
        "irn": data.get("Irn", ""),
        "ack_no": str(data.get("AckNo", "")),
        "ack_date": timezone.now(),
        "signed_qr": data.get("SignedQRCode", ""),
    }


@transaction.atomic
def generate_einvoice(invoice: Invoice, *, actor=None) -> EInvoice:
    """
    Register an e-invoice for `invoice` and persist the IRN/QR + tax breakup.
    Idempotent: an already-GENERATED e-invoice is returned unchanged.
    """
    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
    existing = EInvoice.objects.filter(invoice=invoice).first()
    if existing and existing.status == EInvoice.Status.GENERATED:
        return existing
    if invoice.status == InvoiceStatus.CANCELLED:
        raise ServiceError("Cannot e-invoice a cancelled invoice.")

    if not _supplier_gstin():
        raise ServiceError("Set the school GST number before generating e-invoices.")

    breakup = compute_gst(invoice)
    payload = build_payload(invoice, breakup)

    try:
        result = (
            _register_with_irp(payload)
            if einvoice_enabled()
            else _mock_registration(invoice, payload)
        )
    except ServiceError as exc:
        ei = existing or EInvoice(invoice=invoice)
        ei.status = EInvoice.Status.FAILED
        ei.error = str(exc)[:255]
        ei.payload = payload
        ei.save()
        log.error(
            "einvoice failed invoice=%s error=%s",
            invoice.invoice_number,
            exc,
            **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="generate_einvoice"),
        )
        raise

    ei = existing or EInvoice(invoice=invoice)
    ei.status = EInvoice.Status.GENERATED
    ei.irn = result["irn"]
    ei.ack_no = result["ack_no"]
    ei.ack_date = result["ack_date"]
    ei.signed_qr = result["signed_qr"]
    ei.taxable_value = breakup["taxable_value"]
    ei.cgst = breakup["cgst"]
    ei.sgst = breakup["sgst"]
    ei.igst = breakup["igst"]
    ei.total_tax = breakup["total_tax"]
    ei.payload = payload
    ei.error = ""
    ei.save()

    log.info(
        "einvoice generated invoice=%s irn=%s tax=%s live=%s",
        invoice.invoice_number,
        ei.irn[:12],
        ei.total_tax,
        einvoice_enabled(),
        **ctx(user=getattr(actor, "id", "-"), entity=invoice.id, action="generate_einvoice"),
    )
    record_audit(
        action="einvoice.generated",
        entity=invoice,
        summary=f"E-invoice IRN {ei.irn[:16]}… for {invoice.invoice_number} (tax {ei.total_tax})",
        actor=actor,
    )
    return ei
