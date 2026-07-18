import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services import ServiceError

from .models import Invoice, Payment
from .selectors import collection_dashboard, collection_stats
from .serializers import InvoiceSerializer, PaymentSerializer
from .services import create_invoice, record_payment
from .tasks import generate_invoice_pdf


class CollectionStatsView(APIView):
    """KPI tiles for the fee-collection dashboard."""

    def get(self, request):
        return Response(collection_stats())


class CollectionDashboardView(APIView):
    """Full main dashboard: KPIs, monthly, category breakdown, upcoming dues."""

    def get(self, request):
        return Response(collection_dashboard())


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

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
            currency=data.get("currency", "USD"),
            actor=request.user,
        )
        out = self.get_serializer(invoice)
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def generate_pdf(self, request, pk=None):
        """Kick off async PDF generation (MinIO-backed)."""
        generate_invoice_pdf.delay(self.get_object().id)
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related("invoice")
        invoice = self.request.query_params.get("invoice")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        return qs

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
