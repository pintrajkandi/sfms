import uuid

from rest_framework import serializers

from apps.fees.models import FeeType

from .models import (
    AppliedDiscount,
    BankStatement,
    BankStatementLine,
    CreditNote,
    EInvoice,
    Installment,
    Invoice,
    InvoiceLine,
    Mandate,
    MandateCharge,
    Payment,
    PaymentPlan,
    Refund,
)


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


class InstallmentSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Installment
        fields = (
            "id",
            "sequence",
            "due_date",
            "amount",
            "amount_paid",
            "balance",
            "status",
        )


class PaymentPlanSerializer(serializers.ModelSerializer):
    installments = InstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = PaymentPlan
        fields = ("id", "invoice", "status", "installments", "created_at")
        read_only_fields = fields


class RefundSerializer(serializers.ModelSerializer):
    idempotency_key = serializers.CharField(required=False)

    class Meta:
        model = Refund
        fields = (
            "id",
            "invoice",
            "payment",
            "amount",
            "currency",
            "method",
            "reason",
            "status",
            "idempotency_key",
            "processed_by",
            "created_at",
        )
        read_only_fields = ("currency", "status", "processed_by", "created_at")

    def validate_idempotency_key(self, value):
        return value or uuid.uuid4().hex


class CreditNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditNote
        fields = (
            "id",
            "invoice",
            "credit_note_number",
            "amount",
            "currency",
            "kind",
            "reason",
            "issued_by",
            "created_at",
        )
        read_only_fields = ("credit_note_number", "currency", "issued_by", "created_at")


class AppliedDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppliedDiscount
        fields = ("id", "rule", "code", "name", "kind", "amount")
        read_only_fields = fields


class EInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EInvoice
        fields = (
            "id",
            "status",
            "irn",
            "ack_no",
            "ack_date",
            "signed_qr",
            "taxable_value",
            "cgst",
            "sgst",
            "igst",
            "total_tax",
            "error",
            "created_at",
        )
        read_only_fields = fields


class BankStatementLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankStatementLine
        fields = (
            "id",
            "statement",
            "txn_date",
            "description",
            "reference",
            "amount",
            "status",
            "payment",
        )
        read_only_fields = ("status", "payment")


class BankStatementSerializer(serializers.ModelSerializer):
    line_count = serializers.IntegerField(source="lines.count", read_only=True)

    class Meta:
        model = BankStatement
        fields = ("id", "label", "account_ref", "line_count", "imported_by", "created_at")
        read_only_fields = ("imported_by", "created_at")


class MandateChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MandateCharge
        fields = (
            "id",
            "invoice",
            "amount",
            "currency",
            "status",
            "gateway_payment_id",
            "payment",
            "error",
            "created_at",
        )
        read_only_fields = fields


class MandateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    charges = MandateChargeSerializer(many=True, read_only=True)

    class Meta:
        model = Mandate
        fields = (
            "id",
            "student",
            "student_name",
            "status",
            "frequency",
            "max_amount",
            "currency",
            "payer_vpa",
            "gateway_ref",
            "auth_url",
            "start_on",
            "next_charge_on",
            "charges",
            "created_at",
        )
        read_only_fields = (
            "status",
            "gateway_ref",
            "auth_url",
            "next_charge_on",
            "created_at",
        )


class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    academic_year_label = serializers.SerializerMethodField()
    payment_plan = PaymentPlanSerializer(read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    credit_notes = CreditNoteSerializer(many=True, read_only=True)
    applied_discounts = AppliedDiscountSerializer(many=True, read_only=True)
    einvoice = EInvoiceSerializer(read_only=True)

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
            "adjustment_amount",
            "late_fee_amount",
            "total",
            "amount_paid",
            "balance",
            "lines",
            "payment_plan",
            "refunds",
            "credit_notes",
            "applied_discounts",
            "einvoice",
            "place_of_supply",
            "pdf",
            "created_at",
        )
        read_only_fields = (
            "invoice_number",
            "status",
            "subtotal",
            "adjustment_amount",
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
            "signature",
            "signed_hash",
            "signed_at",
            "created_at",
        )
        read_only_fields = (
            "status",
            "currency",
            "recorded_by",
            "signature",
            "signed_hash",
            "signed_at",
            "created_at",
        )

    def validate_idempotency_key(self, value):
        return value or uuid.uuid4().hex
