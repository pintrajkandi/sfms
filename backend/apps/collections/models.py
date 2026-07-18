"""Invoices & payments — the money core (CLAUDE.md — Invoices, Payments)."""

from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    PARTIAL = "partial", "Partial"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Credit Card"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    PAYPAL = "paypal", "PayPal"
    UPI = "upi", "UPI"
    CHEQUE = "cheque", "Cheque"
    RAZORPAY = "razorpay", "Razorpay"


class Invoice(TimeStampedModel):
    invoice_number = models.CharField(max_length=32, unique=True)
    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="invoices"
    )
    academic_year = models.ForeignKey(
        "schools.AcademicYear", on_delete=models.PROTECT, null=True, blank=True
    )
    status = models.CharField(
        max_length=12,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True,
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")

    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    # Money — all Decimal. Totals are recomputed by services, never by the view.
    subtotal = money_field()
    discount_amount = money_field()
    late_fee_amount = money_field()
    total = money_field()
    amount_paid = money_field()

    pdf = models.FileField(upload_to="invoices/", null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self) -> str:
        return self.invoice_number

    @property
    def balance(self):
        return self.total - self.amount_paid


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    fee_type = models.ForeignKey("fees.FeeType", on_delete=models.PROTECT)
    description = models.CharField(max_length=200, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = money_field()
    amount = money_field()

    def __str__(self) -> str:
        return f"{self.description or self.fee_type.name} x{self.quantity}"


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        RECORDED = "recorded", "Recorded"
        VOID = "void", "Void"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RECORDED)
    paid_at = models.DateTimeField()

    # Idempotency: a repeated submit with the same key is a no-op (CLAUDE.md §5).
    idempotency_key = models.CharField(max_length=64, unique=True)

    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-paid_at",)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency} → {self.invoice_id}"
