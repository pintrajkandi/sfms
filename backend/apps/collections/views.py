import json
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import connection
from django_tenants.utils import schema_context
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.export import export_response
from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

from . import assistant, banking, gateway, mandates, signatures
from .gst import generate_einvoice
from .models import (
    BankStatement,
    BankStatementLine,
    Invoice,
    Mandate,
    Payment,
    PaymentPlan,
)
from .selectors import (
    collection_breakdown,
    collection_dashboard,
    collection_risk_report,
    collection_stats,
    defaulter_report,
)
from .serializers import (
    BankStatementLineSerializer,
    BankStatementSerializer,
    CreditNoteSerializer,
    EInvoiceSerializer,
    InvoiceSerializer,
    MandateSerializer,
    PaymentPlanSerializer,
    PaymentSerializer,
    RefundSerializer,
)
from .services import (
    create_invoice,
    create_payment_plan,
    issue_credit_note,
    record_payment,
    record_refund,
)
from .tasks import generate_invoice_pdf

log = get_logger("collections.views")


class CollectionStatsView(APIView):
    """KPI tiles for the fee-collection dashboard."""

    def get(self, request):
        return Response(collection_stats())


class CollectionDashboardView(APIView):
    """Full main dashboard: KPIs, monthly, category breakdown, upcoming dues."""

    def get(self, request):
        return Response(collection_dashboard())


class DefaultersView(APIView):
    """Defaulter / aging report — JSON, or CSV/XLSX with ?format=."""

    def get(self, request):
        report = defaulter_report()
        fmt = request.query_params.get("fmt")
        if fmt in ("csv", "xlsx"):
            headers = [
                "Student",
                "Student ID",
                "Grade",
                "Outstanding",
                "Days Overdue",
                "Oldest Due",
                "Bucket",
                "Invoices",
            ]
            rows = [
                [
                    d["student"],
                    d["student_id"],
                    d["grade"],
                    d["outstanding"],
                    d["days_overdue"],
                    d["oldest_due"],
                    d["bucket"],
                    d["invoices"],
                ]
                for d in report["defaulters"]
            ]
            return export_response(fmt, "defaulters", headers, rows)
        return Response(report)


class CollectionRiskView(APIView):
    """Predictive collections — students ranked by likelihood of not paying."""

    def get(self, request):
        limit = int(request.query_params.get("limit", 100))
        return Response(collection_risk_report(limit=limit))


class CollectionBreakdownView(APIView):
    """Collections grouped by class, by employee and by method."""

    def get(self, request):
        from datetime import date

        def _parse(v):
            try:
                return date.fromisoformat(v) if v else None
            except ValueError:
                return None

        return Response(
            collection_breakdown(
                since=_parse(request.query_params.get("since")),
                until=_parse(request.query_params.get("until")),
            )
        )


class StudentLedgerView(APIView):
    """Running fee statement for one student (?student=<id>)."""

    def get(self, request):
        from apps.students.models import Student

        from .ledgers import student_ledger

        student_id = request.query_params.get("student")
        student = Student.objects.filter(pk=student_id).first() if student_id else None
        if student is None:
            raise ValidationError("A valid 'student' id is required.")
        return Response(student_ledger(student=student))


class ParentLedgerView(APIView):
    """Combined statement across a guardian's children (?student=<id> or ?phone=)."""

    def get(self, request):
        from apps.students.models import Student

        from .ledgers import parent_ledger

        phone = (request.query_params.get("phone") or "").strip()
        name = ""
        if not phone:
            student = Student.objects.filter(pk=request.query_params.get("student")).first()
            if student is None:
                raise ValidationError("Provide a 'student' id or guardian 'phone'.")
            phone = student.guardian_phone
            name = student.guardian_name

        kids = Student.objects.alive()
        if phone:
            kids = kids.filter(guardian_phone=phone)
        elif name:
            kids = kids.filter(guardian_name=name)
        else:
            raise ValidationError("This student has no guardian phone on file.")
        if not name:
            first = kids.first()
            name = first.guardian_name if first else ""
        return Response(
            parent_ledger(students=list(kids), guardian_name=name, guardian_phone=phone)
        )


class CollectionAssistantView(APIView):
    """
    NL collections assistant. POST {question}. Answers from the risk report via
    Claude when configured, else a deterministic rule-based summary.
    """

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        if not question:
            raise ValidationError("A question is required.")
        return Response(assistant.ask(question))

    def get(self, request):
        return Response({"enabled": assistant.assistant_enabled()})


class SigningKeyView(APIView):
    """Publish the tenant's active receipt-signing public key (for verifiers)."""

    def get(self, request):
        key = signatures.get_active_key()
        return Response(
            {"algorithm": key.algorithm, "public_pem": key.public_pem, "key_id": key.id}
        )


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    rbac_resource = "invoices"

    def get_queryset(self):
        qs = Invoice.objects.select_related("student").prefetch_related("lines")
        student = self.request.query_params.get("student")
        state = self.request.query_params.get("status")
        if student:
            qs = qs.filter(student_id=student)
        if state:
            qs = qs.filter(status=state)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invoice = create_invoice(
            student=data["student"],
            lines=data["lines"],
            academic_year=data.get("academic_year"),
            due_date=data.get("due_date"),
            discount_amount=data.get("discount_amount", 0),
            late_fee_amount=data.get("late_fee_amount", 0),
            currency=data.get("currency", "INR"),
            actor=request.user,
        )
        out = self.get_serializer(invoice)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def generate_pdf(self, request, pk=None):
        """Kick off async PDF generation (MinIO-backed)."""
        generate_invoice_pdf.delay(self.get_object().id)
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["get", "post"], url_path="payment-plan")
    def payment_plan(self, request, pk=None):
        """GET the invoice's instalment plan, or POST to create one."""
        invoice = self.get_object()
        if request.method == "GET":
            plan = PaymentPlan.objects.filter(invoice=invoice).first()
            if plan is None:
                return Response({"detail": "No payment plan."}, status=status.HTTP_404_NOT_FOUND)
            return Response(PaymentPlanSerializer(plan).data)

        data = request.data
        try:
            plan = create_payment_plan(
                invoice=invoice,
                count=data.get("count"),
                first_due_date=data.get("first_due_date"),
                frequency=data.get("frequency", "monthly"),
                schedule=data.get("schedule"),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(PaymentPlanSerializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def refund(self, request, pk=None):
        """Return cash to the payer (reduces amount_paid; idempotent)."""
        invoice = self.get_object()
        serializer = RefundSerializer(data={**request.data, "invoice": invoice.id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            refund = record_refund(
                invoice=invoice,
                amount=data["amount"],
                method=data["method"],
                idempotency_key=data.get("idempotency_key") or uuid.uuid4().hex,
                reason=data.get("reason", ""),
                payment=data.get("payment"),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="credit-note")
    def credit_note(self, request, pk=None):
        """Issue a credit note (reduces the bill; no cash movement)."""
        invoice = self.get_object()
        serializer = CreditNoteSerializer(data={**request.data, "invoice": invoice.id})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            note = issue_credit_note(
                invoice=invoice,
                amount=data["amount"],
                kind=data.get("kind", "adjustment"),
                reason=data.get("reason", ""),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(CreditNoteSerializer(note).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"])
    def einvoice(self, request, pk=None):
        """GET the invoice's e-invoice (IRN/QR), or POST to register one."""
        invoice = self.get_object()
        if request.method == "GET":
            ei = getattr(invoice, "einvoice", None)
            if ei is None:
                return Response({"detail": "No e-invoice."}, status=status.HTTP_404_NOT_FOUND)
            return Response(EInvoiceSerializer(ei).data)
        try:
            ei = generate_einvoice(invoice, actor=request.user)
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(EInvoiceSerializer(ei).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    rbac_resource = "payments"

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice__student").order_by("-paid_at")
        invoice = self.request.query_params.get("invoice")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        term = (self.request.query_params.get("search") or "").strip()
        if term:
            from django.db.models import Q

            qs = qs.filter(
                Q(invoice__student__first_name__icontains=term)
                | Q(invoice__student__last_name__icontains=term)
                | Q(invoice__student__student_id__icontains=term)
                | Q(reference__icontains=term)
            )
        return qs

    @action(detail=True, methods=["get"])
    def receipt(self, request, pk=None):
        """Branded receipt data (with QR + barcode) for printing/sharing."""
        from .receipts import receipt_data

        return Response(receipt_data(self.get_object()))

    @action(detail=False, methods=["get"])
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv")
        headers = [
            "Date",
            "Student",
            "Grade",
            "Fee Type",
            "Amount",
            "Method",
            "Reference",
            "Invoice",
            "Status",
        ]
        rows = [
            [
                p.paid_at.date().isoformat(),
                p.invoice.student.full_name,
                p.invoice.student.grade,
                (p.invoice.lines.first().fee_type.name if p.invoice.lines.exists() else ""),
                str(p.amount),
                p.method,
                p.reference,
                p.invoice.invoice_number,
                p.invoice.status,
            ]
            for p in self.get_queryset().order_by("-paid_at")
        ]
        return export_response(fmt, "payments", headers, rows)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            payment = record_payment(
                invoice=data["invoice"],
                amount=data["amount"],
                method=data["method"],
                # Client may omit it; generate one so single-submit still works.
                idempotency_key=data.get("idempotency_key") or uuid.uuid4().hex,
                paid_at=data.get("paid_at"),
                reference=data.get("reference", ""),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        out = self.get_serializer(payment)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def signature(self, request, pk=None):
        """Verify a receipt's digital signature and return the public key."""
        payment = self.get_object()
        result = signatures.verify_receipt(payment)
        result["public_pem"] = payment.signing_key.public_pem if payment.signing_key else ""
        result["signed_hash"] = payment.signed_hash
        return Response(result)

    @action(detail=True, methods=["post"])
    def bounce(self, request, pk=None):
        """Dishonour a cheque payment: void it, reverse the credit, levy a charge."""
        payment = self.get_object()
        try:
            bounce = banking.bounce_cheque(
                payment=payment,
                reason=request.data.get("reason", ""),
                charge=request.data.get("charge"),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {
                "status": "bounced",
                "payment": payment.id,
                "invoice": bounce.invoice_id,
                "charge": str(bounce.charge),
            },
            status=status.HTTP_201_CREATED,
        )


class BankStatementViewSet(viewsets.ModelViewSet):
    """
    Import a bank statement (POST rows) and auto-reconcile credit lines to
    recorded payments. Lines are exposed read-only for the unmatched worklist.
    """

    serializer_class = BankStatementSerializer
    rbac_resource = "bank-statements"

    def get_queryset(self):
        return BankStatement.objects.all()

    def create(self, request, *args, **kwargs):
        rows = request.data.get("lines") or []
        if not rows:
            raise ValidationError("At least one statement line is required.")
        try:
            statement = banking.import_bank_statement(
                label=request.data.get("label", "Statement"),
                account_ref=request.data.get("account_ref", ""),
                rows=rows,
                actor=request.user,
            )
        except (KeyError, ServiceError) as exc:
            raise ValidationError(f"Invalid statement rows: {exc}") from exc
        return Response(BankStatementSerializer(statement).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reconcile(self, request, pk=None):
        result = banking.auto_reconcile(statement=self.get_object(), actor=request.user)
        return Response(result)

    @action(detail=False, methods=["post"], url_path="reconcile-all")
    def reconcile_all(self, request):
        return Response(banking.auto_reconcile(actor=request.user))

    @action(detail=False, methods=["get"])
    def lines(self, request):
        qs = BankStatementLine.objects.select_related("statement", "payment")
        state = request.query_params.get("status")
        if state:
            qs = qs.filter(status=state)
        page = self.paginate_queryset(qs)
        serializer = BankStatementLineSerializer(page or qs, many=True)
        return self.get_paginated_response(serializer.data) if page else Response(serializer.data)


class MandateViewSet(viewsets.ModelViewSet):
    """UPI Autopay / e-mandates: create, authorise, cancel, and manually charge."""

    serializer_class = MandateSerializer
    rbac_resource = "mandates"

    def get_queryset(self):
        qs = Mandate.objects.select_related("student").prefetch_related("charges")
        student = self.request.query_params.get("student")
        state = self.request.query_params.get("status")
        if student:
            qs = qs.filter(student_id=student)
        if state:
            qs = qs.filter(status=state)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            mandate = mandates.create_mandate(
                student=d["student"],
                max_amount=d["max_amount"],
                frequency=d.get("frequency", Mandate.Frequency.AS_PRESENTED),
                currency=d.get("currency", "INR"),
                payer_vpa=d.get("payer_vpa", ""),
                start_on=d.get("start_on"),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(mandate).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Mark the mandate authorised (payer approved). In prod this is a webhook."""
        try:
            mandate = mandates.activate_mandate(self.get_object(), actor=request.user)
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(mandate).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        mandate = mandates.cancel_mandate(self.get_object(), actor=request.user)
        return Response(self.get_serializer(mandate).data)

    @action(detail=True, methods=["post"])
    def charge(self, request, pk=None):
        """Manually trigger an auto-debit against a specific invoice."""
        invoice = _get_invoice_or_400(request.data.get("invoice"))
        try:
            charge = mandates.charge_mandate(
                mandate=self.get_object(),
                invoice=invoice,
                amount=request.data.get("amount"),
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {"status": charge.status, "charge": charge.id, "payment": charge.payment_id},
            status=status.HTTP_201_CREATED,
        )


# --------------------------------------------------------------------------- #
# Razorpay online-payment endpoints (tenant-scoped). Views stay thin — signature
# checks and order creation live in apps.collections.gateway; crediting the
# invoice goes through record_payment so it is idempotent + auditable.
# --------------------------------------------------------------------------- #
class RazorpayConfigView(APIView):
    """Public config for the checkout widget: is it enabled + the publishable key."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"enabled": gateway.razorpay_enabled(), "key_id": settings.RAZORPAY_KEY_ID})


class RazorpayOrderView(APIView):
    """Create a Razorpay order for an invoice's outstanding balance."""

    def post(self, request):
        if not gateway.razorpay_enabled():
            return Response(
                {"detail": "Online payments not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        invoice = _get_invoice_or_400(request.data.get("invoice"))
        amount = invoice.balance
        if amount <= 0:
            raise ValidationError("Invoice has no outstanding balance.")

        # notes carry the tenant schema so the (tenant-less) webhook can reconcile.
        notes = {"schema": connection.schema_name, "invoice": invoice.id}
        try:
            order = gateway.create_order(amount=amount, receipt=invoice.invoice_number, notes=notes)
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            {
                "order_id": order["id"],
                "amount": order["amount"],  # paise (int)
                "currency": "INR",
                "key_id": settings.RAZORPAY_KEY_ID,
                "invoice": invoice.id,
            }
        )


class RazorpayVerifyView(APIView):
    """Verify a completed client-side checkout and record the payment."""

    def post(self, request):
        if not gateway.razorpay_enabled():
            return Response(
                {"detail": "Online payments not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        data = request.data
        invoice = _get_invoice_or_400(data.get("invoice"))
        order_id = data.get("razorpay_order_id", "")
        payment_id = data.get("razorpay_payment_id", "")
        signature = data.get("razorpay_signature", "")
        if not (order_id and payment_id and signature):
            raise ValidationError("Missing Razorpay verification parameters.")

        ok = gateway.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
        if not ok:
            return Response(
                {"detail": "Invalid payment signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Already reconciled (e.g. the webhook beat us to it, or a double-submit):
        # return the existing payment without re-crediting. Idempotency lives in
        # record_payment, but the balance may now be 0, so short-circuit here.
        payment = Payment.objects.filter(idempotency_key=payment_id).first()
        if payment is None:
            try:
                payment = record_payment(
                    invoice=invoice,
                    amount=invoice.balance,
                    method="razorpay",
                    idempotency_key=payment_id,
                    reference=payment_id,
                    actor=request.user,
                )
            except ServiceError as exc:
                raise ValidationError(str(exc)) from exc
        invoice.refresh_from_db()
        return Response(
            {
                "status": "recorded",
                "payment_id": payment.id,
                "invoice_status": invoice.status,
            }
        )


def _get_invoice_or_400(invoice_id) -> Invoice:
    if not invoice_id:
        raise ValidationError("invoice is required.")
    invoice = Invoice.objects.filter(pk=invoice_id).first()
    if invoice is None:
        raise ValidationError("Invoice not found.")
    return invoice


class RazorpayWebhookView(APIView):
    """
    Auto-reconciliation endpoint (PUBLIC schema — Razorpay hits one host with no
    tenant subdomain). Verifies the webhook signature, then on `payment.captured`
    reads the tenant schema + invoice id from the order/payment `notes`, switches
    into that schema and records the payment via the idempotent record_payment.

    The idempotency_key is the Razorpay payment id, so the webhook and the
    client-side verify call are safe to both fire — only one Payment is created.
    Returns 200 for any valid signature so Razorpay stops retrying; 400 only on a
    bad signature or unconfigured secret.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        if not gateway.razorpay_enabled() or not settings.RAZORPAY_WEBHOOK_SECRET:
            log.warning(
                "razorpay webhook received but gateway not configured",
                **ctx(action="razorpay_webhook"),
            )
            return Response(
                {"detail": "Online payments not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        body = request.body  # raw bytes — required for signature verification
        signature = request.META.get("HTTP_X_RAZORPAY_SIGNATURE", "")
        try:
            valid = gateway.verify_webhook_signature(body, signature)
        except ServiceError:
            return Response(
                {"detail": "Online payments not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not valid:
            log.warning(
                "razorpay webhook signature rejected",
                **ctx(action="razorpay_webhook"),
            )
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            log.warning("razorpay webhook body not JSON", **ctx(action="razorpay_webhook"))
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        if payload.get("event") != "payment.captured":
            # Signature was valid; nothing to do for other events. 200 stops retries.
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        notes = entity.get("notes") or {}
        schema = notes.get("schema")
        invoice_id = notes.get("invoice")
        payment_id = entity.get("id", "")
        amount_paise = entity.get("amount")

        if not (schema and invoice_id and payment_id and amount_paise is not None):
            log.warning(
                "razorpay webhook missing reconciliation notes payment=%s",
                payment_id or "-",
                **ctx(action="razorpay_webhook"),
            )
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)

        amount = Decimal(amount_paise) / Decimal(100)
        try:
            with schema_context(schema):
                invoice = Invoice.objects.filter(pk=invoice_id).first()
                if invoice is None:
                    log.warning(
                        "razorpay webhook invoice not found invoice=%s",
                        invoice_id,
                        **ctx(action="razorpay_webhook"),
                    )
                    return Response({"status": "ignored"}, status=status.HTTP_200_OK)
                payment = record_payment(
                    invoice=invoice,
                    amount=amount,
                    method="razorpay",
                    idempotency_key=payment_id,
                    reference=payment_id,
                )
        except ServiceError as exc:
            # e.g. amount exceeds balance because client-verify already credited it.
            log.warning(
                "razorpay webhook reconcile skipped invoice=%s reason=%s",
                invoice_id,
                exc,
                **ctx(action="razorpay_webhook"),
            )
            return Response({"status": "skipped"}, status=status.HTTP_200_OK)

        log.info(
            "razorpay webhook reconciled invoice=%s payment=%s amount=%s",
            invoice_id,
            payment_id,
            amount,
            **ctx(entity=payment.id, action="razorpay_webhook"),
        )
        return Response({"status": "reconciled"}, status=status.HTTP_200_OK)
