"""
Parent-portal API (CLAUDE.md §5 — thin views; money math + workflow in services).

All endpoints are unauthenticated at the DRF layer (``AllowAny`` + no
authentication classes): the OTP endpoints establish trust, and the data
endpoints carry their own ``X-Parent-Token`` verified in ``services``. The
tenant is *always* the routed schema (CLAUDE.md §3) — the client never supplies
one. Invoice ownership is re-checked against the token's student on every call.
"""

from __future__ import annotations

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collections import gateway, mandates, signatures
from apps.collections.models import Invoice, InvoiceStatus, Mandate, Payment
from apps.collections.selectors import student_fee_summary
from apps.collections.services import record_payment
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO

from .authentication import parent_from_request
from .services import request_otp, verify_otp

log = get_logger("portal")


class _PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []


class _ParentView(_PublicView):
    """Base for token-scoped endpoints — resolves the student or returns 401."""

    def get_student(self, request):
        return parent_from_request(request)


class RequestOtpView(_PublicView):
    def post(self, request):
        request_otp(
            str(request.data.get("student_id", "")).strip(),
            str(request.data.get("phone", "")).strip(),
        )
        # Always 200 regardless of match — no account enumeration.
        return Response({"detail": "If the details match, a code has been sent."})


class VerifyOtpView(_PublicView):
    def post(self, request):
        student_id = str(request.data.get("student_id", "")).strip()
        phone = str(request.data.get("phone", "")).strip()
        otp = str(request.data.get("otp", "")).strip()
        token = verify_otp(student_id, phone, otp)
        if not token:
            return Response(
                {"detail": "Invalid or expired code."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .services import read_token

        student = read_token(token)
        return Response(
            {
                "token": token,
                "student_name": student.full_name if student else "",
                "student_id": student.student_id if student else student_id,
            }
        )


class PortalFeesView(_ParentView):
    def get(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(student_fee_summary(student))


class PortalInvoicesView(_ParentView):
    def get(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        invoices = (
            student.invoices.exclude(status=InvoiceStatus.CANCELLED)
            .prefetch_related("payment_plan__installments")
            .order_by("-created_at")
        )
        payable = [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "total": str(inv.total),
                "amount_paid": str(inv.amount_paid),
                "balance": str(inv.balance),
                "status": inv.status,
                "due_date": inv.due_date,
                "installments": _installments(inv),
            }
            for inv in invoices
            if inv.balance > ZERO
        ]
        return Response(payable)


def _installments(invoice):
    """Instalment schedule for the parent view, if a plan exists."""
    plan = getattr(invoice, "payment_plan", None)
    if plan is None:
        return []
    return [
        {
            "sequence": i.sequence,
            "due_date": i.due_date,
            "amount": str(i.amount),
            "amount_paid": str(i.amount_paid),
            "status": i.status,
        }
        for i in plan.installments.all()
    ]


class PortalAutopayView(_ParentView):
    """UPI Autopay for a student: view the mandate, or set one up."""

    def get(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        m = Mandate.objects.filter(student=student).order_by("-created_at").first()
        if m is None:
            return Response({"mandate": None})
        return Response({"mandate": _mandate_dict(m)})

    def post(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if Mandate.objects.filter(student=student, status=Mandate.Status.ACTIVE).exists():
            return Response(
                {"detail": "Autopay is already active."}, status=status.HTTP_400_BAD_REQUEST
            )

        max_amount = request.data.get("max_amount") or "10000"
        mandate = mandates.create_mandate(student=student, max_amount=max_amount, currency="INR")
        # In dev (no live gateway) there is no external authorisation step — activate
        # so the parent sees Autopay working end-to-end.
        if not gateway.razorpay_enabled():
            mandates.activate_mandate(mandate)
        mandate.refresh_from_db()
        return Response({"mandate": _mandate_dict(mandate)}, status=status.HTTP_201_CREATED)


def _mandate_dict(m) -> dict:
    return {
        "id": m.id,
        "status": m.status,
        "max_amount": str(m.max_amount),
        "currency": m.currency,
        "auth_url": m.auth_url,
        "next_charge_on": m.next_charge_on,
    }


class PortalReceiptsView(_ParentView):
    """Signed receipts for the student's payments (tamper-evident)."""

    def get(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        rows = []
        payments = (
            Payment.objects.filter(invoice__student=student, status=Payment.Status.RECORDED)
            .select_related("invoice", "signing_key")
            .order_by("-paid_at")[:50]
        )
        for p in payments:
            verify = signatures.verify_receipt(p)
            rows.append(
                {
                    "id": p.id,
                    "invoice_number": p.invoice.invoice_number,
                    "amount": str(p.amount),
                    "currency": p.currency,
                    "method": p.method,
                    "paid_at": p.paid_at,
                    "signed": verify["signed"],
                    "valid": verify["valid"],
                }
            )
        return Response(rows)


def _owned_invoice(student, invoice_id):
    """Load an invoice that belongs to this student, or None (→ 404)."""
    if invoice_id in (None, ""):
        return None
    inv = Invoice.objects.filter(pk=invoice_id).first()
    if inv is None or inv.student_id != student.pk:
        return None
    return inv


class PortalPayOrderView(_ParentView):
    def post(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        invoice = _owned_invoice(student, request.data.get("invoice"))
        if invoice is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        amount = invoice.balance
        if amount <= ZERO:
            return Response(
                {"detail": "Nothing to pay on this invoice."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not gateway.razorpay_enabled():
            return Response(
                {"detail": "Online payments not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        order = gateway.create_order(
            amount=amount,
            receipt=invoice.invoice_number,
            notes={"schema": connection.schema_name, "invoice": invoice.id},
        )
        return Response(
            {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
            }
        )


class PortalPayVerifyView(_ParentView):
    def post(self, request):
        student = self.get_student(request)
        if student is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        invoice = _owned_invoice(student, request.data.get("invoice"))
        if invoice is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payment_id = str(request.data.get("razorpay_payment_id", ""))
        params = {
            "razorpay_order_id": request.data.get("razorpay_order_id"),
            "razorpay_payment_id": payment_id,
            "razorpay_signature": request.data.get("razorpay_signature"),
        }
        if not gateway.verify_payment_signature(params):
            return Response(
                {"detail": "Payment verification failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Idempotent reconciliation: same razorpay_payment_id is credited once.
        if not Payment.objects.filter(idempotency_key=payment_id).exists():
            record_payment(
                invoice=invoice,
                amount=invoice.balance,
                method="razorpay",
                idempotency_key=payment_id,
                reference=payment_id,
            )
            log.info(
                "parent payment recorded invoice=%s",
                invoice.invoice_number,
                **ctx(entity=invoice.id, action="portal_pay_verify"),
            )

        invoice.refresh_from_db()
        return Response({"status": "recorded", "invoice_status": invoice.status})
