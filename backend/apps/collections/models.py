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
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")

    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)

    # GST place of supply (buyer state). Blank → the school's own state (B2C intra).
    place_of_supply = models.CharField(max_length=64, blank=True)

    # Money — all Decimal. Totals are recomputed by services, never by the view.
    subtotal = money_field()
    discount_amount = money_field()
    # Post-issue credits (credit notes / write-offs) accrue here and reduce total.
    adjustment_amount = money_field()
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
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    # Auto-generated, purely numeric receipt/transaction number (assigned by the
    # service on record — see collections.services.record_payment). Unique per tenant.
    receipt_number = models.CharField(max_length=20, blank=True, db_index=True)
    reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RECORDED)
    paid_at = models.DateTimeField()

    # Idempotency: a repeated submit with the same key is a no-op (CLAUDE.md §5).
    idempotency_key = models.CharField(max_length=64, unique=True)

    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Digital signature over the receipt payload (Ed25519 — see collections.signatures).
    signature = models.TextField(blank=True)  # base64 signature
    signed_hash = models.CharField(max_length=64, blank=True)  # sha256 of payload
    signing_key = models.ForeignKey(
        "collections.SigningKey", on_delete=models.SET_NULL, null=True, blank=True
    )
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-paid_at",)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency} → {self.invoice_id}"


class SigningKey(TimeStampedModel):
    """
    Per-tenant Ed25519 keypair used to digitally sign receipts. One active key at
    a time; rotating creates a new active key (old ones stay for verification).
    The private key is stored PEM-encoded — in production keep it in a KMS/secret
    store, not the DB.
    """

    label = models.CharField(max_length=64, default="default")
    algorithm = models.CharField(max_length=20, default="ed25519")
    public_pem = models.TextField()
    private_pem = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"SigningKey {self.label} ({self.algorithm})"


class PaymentPlan(TimeStampedModel):
    """An instalment schedule for a single invoice (CLAUDE.md — Payments)."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="payment_plan")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Plan · {self.invoice.invoice_number} ({self.status})"


class Installment(TimeStampedModel):
    """One scheduled instalment. Allocation is derived from invoice.amount_paid."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"

    plan = models.ForeignKey(PaymentPlan, on_delete=models.CASCADE, related_name="installments")
    sequence = models.PositiveIntegerField()
    due_date = models.DateField()
    amount = money_field()
    amount_paid = money_field()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )

    class Meta:
        ordering = ("plan", "sequence")
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "sequence"], name="uniq_installment_plan_sequence"
            )
        ]

    def __str__(self) -> str:
        return f"#{self.sequence} {self.amount} due {self.due_date}"

    @property
    def balance(self):
        return self.amount - self.amount_paid


class Refund(TimeStampedModel):
    """
    Cash returned to the payer (overpayment, withdrawal). Reduces the invoice's
    amount_paid and is idempotent via a unique key (CLAUDE.md §5).
    """

    class Status(models.TextChoices):
        PROCESSED = "processed", "Processed"
        VOID = "void", "Void"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="refunds")
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds"
    )
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    method = models.CharField(max_length=16, choices=PaymentMethod.choices)
    reason = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PROCESSED)
    idempotency_key = models.CharField(max_length=64, unique=True)
    processed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Refund {self.amount} {self.currency} ← {self.invoice_id}"


class CreditNote(TimeStampedModel):
    """
    A post-issue credit that reduces what the student owes WITHOUT cash movement:
    corrections, write-offs, goodwill concessions. Accrues into
    Invoice.adjustment_amount.
    """

    class Kind(models.TextChoices):
        ADJUSTMENT = "adjustment", "Adjustment"
        CORRECTION = "correction", "Correction"
        WRITE_OFF = "write_off", "Write-off"
        CONCESSION = "concession", "Concession"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="credit_notes")
    credit_note_number = models.CharField(max_length=32, unique=True)
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.ADJUSTMENT)
    reason = models.CharField(max_length=255, blank=True)
    issued_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.credit_note_number} · {self.amount} {self.currency}"


class EInvoice(TimeStampedModel):
    """
    GST e-invoice registration for an invoice: the IRN + signed QR obtained from
    the Invoice Registration Portal (IRP), with the extracted CGST/SGST/IGST
    breakup. Fee amounts are tax-inclusive, so tax is extracted, not added.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATED = "generated", "Generated"
        CANCELLED = "cancelled", "Cancelled"
        FAILED = "failed", "Failed"

    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="einvoice")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    irn = models.CharField(max_length=72, blank=True, db_index=True)  # Invoice Reference Number
    ack_no = models.CharField(max_length=32, blank=True)
    ack_date = models.DateTimeField(null=True, blank=True)
    signed_qr = models.TextField(blank=True)  # QR payload from the IRP

    # Extracted tax breakup (from tax-inclusive line amounts).
    taxable_value = money_field()
    cgst = money_field()
    sgst = money_field()
    igst = money_field()
    total_tax = money_field()

    payload = models.JSONField(default=dict, blank=True)  # the JSON sent to the IRP
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"E-Invoice {self.invoice.invoice_number} ({self.status})"


class BankStatement(TimeStampedModel):
    """An imported bank statement file (one per upload)."""

    label = models.CharField(max_length=120)
    account_ref = models.CharField(max_length=64, blank=True)  # last-4 / nickname
    imported_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.label} ({self.account_ref})"


class BankStatementLine(TimeStampedModel):
    """
    One row of a bank statement, matched (or not) to a Payment during
    reconciliation. Only credit (money-in) lines are matched to fee payments.
    """

    class Status(models.TextChoices):
        UNMATCHED = "unmatched", "Unmatched"
        MATCHED = "matched", "Matched"
        IGNORED = "ignored", "Ignored"

    statement = models.ForeignKey(BankStatement, on_delete=models.CASCADE, related_name="lines")
    txn_date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=100, blank=True)  # UTR / cheque no / ref
    amount = money_field()  # positive = credit (money in), negative = debit
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.UNMATCHED, db_index=True
    )
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="bank_lines"
    )

    class Meta:
        ordering = ("txn_date", "id")

    def __str__(self) -> str:
        return f"{self.txn_date} {self.amount} [{self.status}]"


class ChequeBounce(TimeStampedModel):
    """
    A dishonoured cheque payment. Voids the payment, reverses the credit, and
    optionally levies a bounce charge (added to the invoice as a late fee).
    """

    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="bounce")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="cheque_bounces")
    reason = models.CharField(max_length=255, blank=True)
    charge = money_field()
    recorded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Bounce {self.payment_id} on {self.invoice_id}"


class Mandate(TimeStampedModel):
    """
    A UPI Autopay / e-mandate authorising recurring auto-debit for a student's
    fees. The gateway (Razorpay) holds the real mandate; we store its token +
    lifecycle. Auto-debits within `max_amount` are attempted by dispatch_autopay.
    """

    class Status(models.TextChoices):
        CREATED = "created", "Created"  # awaiting payer authorisation
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    class Frequency(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        AS_PRESENTED = "as_presented", "As presented"

    student = models.ForeignKey(
        "students.Student", on_delete=models.PROTECT, related_name="mandates"
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.CREATED, db_index=True
    )
    frequency = models.CharField(
        max_length=14, choices=Frequency.choices, default=Frequency.AS_PRESENTED
    )
    # Per-debit ceiling the payer authorised. Auto-debits never exceed this.
    max_amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")

    payer_vpa = models.CharField(max_length=100, blank=True)  # UPI id, e.g. name@bank
    # Gateway identifiers (Razorpay subscription/token/customer ids or a dev mock).
    gateway_ref = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_customer = models.CharField(max_length=100, blank=True)
    auth_url = models.URLField(blank=True)  # where the payer approves the mandate

    start_on = models.DateField(null=True, blank=True)
    next_charge_on = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Mandate {self.student_id} ({self.status})"


class MandateCharge(TimeStampedModel):
    """One auto-debit attempt against a mandate, linked to the invoice + payment."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE, related_name="charges")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="mandate_charges")
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    # Idempotency: one charge per (mandate, invoice, period) key.
    idempotency_key = models.CharField(max_length=80, unique=True)
    payment = models.ForeignKey(
        Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="mandate_charges"
    )
    error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Charge {self.amount} {self.currency} [{self.status}]"


class AppliedDiscount(TimeStampedModel):
    """
    Audit of a concession applied to an invoice at creation (fees.DiscountRule).
    The rule may be null if it was later removed; name/kind are captured inline.
    """

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="applied_discounts")
    rule = models.ForeignKey("fees.DiscountRule", on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=16)
    amount = money_field()

    class Meta:
        ordering = ("-amount",)

    def __str__(self) -> str:
        return f"{self.name} −{self.amount} on {self.invoice_id}"
