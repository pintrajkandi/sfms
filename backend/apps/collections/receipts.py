"""
Fee receipt rendering — school-branded receipt data with a QR code (for digital
verification) and a Code-128 barcode of the receipt number. Pure-Python SVG, so
no headless-browser/PDF toolchain is required.
"""

from __future__ import annotations

import base64
import io


def _svg_data_uri(svg_bytes: bytes) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_bytes).decode()


def qr_data_uri(text: str) -> str:
    import segno

    buf = io.BytesIO()
    segno.make(text, error="m").save(buf, kind="svg", scale=3, border=1)
    return _svg_data_uri(buf.getvalue())


def barcode_data_uri(text: str) -> str:
    from barcode import Code128
    from barcode.writer import SVGWriter

    buf = io.BytesIO()
    Code128(text, writer=SVGWriter()).write(buf, options={"module_height": 8.0, "font_size": 0})
    return _svg_data_uri(buf.getvalue())


def receipt_number(payment) -> str:
    # Prefer the auto-generated numeric receipt number; fall back to the legacy
    # composite form for any pre-existing payment that predates the field.
    return payment.receipt_number or f"{payment.invoice.invoice_number}-R{payment.id}"


def receipt_data(payment) -> dict:
    """Everything needed to render/print a branded receipt for one payment."""
    from apps.schools.models import SchoolSettings

    settings = SchoolSettings.objects.first()
    invoice = payment.invoice
    student = invoice.student
    number = receipt_number(payment)

    # Compact QR payload for verification (receipt no · amount · signed hash).
    verify_payload = f"{number}|{payment.amount}|{payment.signed_hash or 'unsigned'}"

    school = {
        "name": getattr(settings, "name", "") if settings else "",
        "logo": settings.logo.url if settings and settings.logo else "",
        "address": getattr(settings, "street_address", "") if settings else "",
        "phone": getattr(settings, "primary_phone", "") if settings else "",
        "email": getattr(settings, "official_email", "") if settings else "",
        "footer": getattr(settings, "invoice_footer_note", "") if settings else "",
    }
    return {
        "receipt_number": number,
        "date": payment.paid_at.date().isoformat() if payment.paid_at else "",
        "amount": str(payment.amount),
        "currency": payment.currency,
        "method": payment.method,
        "reference": payment.reference,
        "verified": bool(payment.signed_hash),
        "school": school,
        "student": {
            "name": student.full_name,
            "student_id": student.student_id,
            "grade": student.grade,
            "section": student.section,
            "guardian": student.guardian_name,
        },
        "invoice": {
            "number": invoice.invoice_number,
            "total": str(invoice.total),
            "amount_paid": str(invoice.amount_paid),
            "balance": str(invoice.balance),
        },
        "qr": qr_data_uri(verify_payload),
        "barcode": barcode_data_uri(number.replace("-", "")),
    }
