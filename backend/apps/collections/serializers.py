import uuid

from rest_framework import serializers

from apps.fees.models import FeeType

from .models import Invoice, InvoiceLine, Payment


class InvoiceLineSerializer(serializers.ModelSerializer):
    fee_type = serializers.PrimaryKeyRelatedField(queryset=FeeType.objects.all())
    fee_type_name = serializers.CharField(source="fee_type.name", read_only=True)
    fee_type_category = serializers.CharField(source="fee_type.category.name", read_only=True)

    class Meta:
        model = InvoiceLine
        fields = (
            "id",
            "fee_type",
            "fee_type_name",
            "fee_type_category",
            "description",
            "quantity",
            "unit_price",
            "amount",
        )
        read_only_fields = ("amount",)


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    academic_year_label = serializers.SerializerMethodField()

    def get_academic_year_label(self, obj) -> str:
        return obj.academic_year.label if obj.academic_year_id else ""

    class Meta:
        model = Invoice
        fields = (
            "id",
            "invoice_number",
            "student",
            "student_name",
            "academic_year",
            "academic_year_label",
            "status",
            "currency",
            "issue_date",
            "due_date",
            "subtotal",
            "discount_amount",
            "late_fee_amount",
            "total",
            "amount_paid",
            "balance",
            "lines",
            "pdf",
            "created_at",
        )
        read_only_fields = (
            "invoice_number",
            "status",
            "subtotal",
            "total",
            "amount_paid",
            "issue_date",
            "pdf",
        )


class PaymentSerializer(serializers.ModelSerializer):
    # Client supplies a key so retries don't double-charge; default one for convenience.
    idempotency_key = serializers.CharField(required=False)
    # Optional — the service defaults to "now" when omitted.
    paid_at = serializers.DateTimeField(required=False)
    # Read-side enrichment for the recent-payments table.
    student_name = serializers.CharField(source="invoice.student.full_name", read_only=True)
    student_grade = serializers.CharField(source="invoice.student.grade", read_only=True)
    invoice_status = serializers.CharField(source="invoice.status", read_only=True)
    fee_type = serializers.SerializerMethodField()

    def get_fee_type(self, obj) -> str:
        line = obj.invoice.lines.first()
        return line.fee_type.name if line else ""

    class Meta:
        model = Payment
        fields = (
            "id",
            "invoice",
            "amount",
            "currency",
            "method",
            "reference",
            "status",
            "paid_at",
            "student_name",
            "student_grade",
            "invoice_status",
            "fee_type",
            "idempotency_key",
            "recorded_by",
            "created_at",
        )
        read_only_fields = ("status", "currency", "recorded_by", "created_at")

    def validate_idempotency_key(self, value):
        return value or uuid.uuid4().hex
