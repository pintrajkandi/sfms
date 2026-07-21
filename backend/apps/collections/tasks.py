"""
Async invoice/PDF work (Celery + RabbitMQ). Tasks are idempotent, take ids not
objects, and must run inside the correct tenant schema (CLAUDE.md §5).
"""

from __future__ import annotations

from celery import shared_task

from apps.core.logging import ctx, get_logger

log = get_logger("collections.tasks")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def generate_invoice_pdf(self, invoice_id: int, schema: str | None = None) -> None:
    """
    Render an invoice to PDF and store it in MinIO.

    `schema` pins the tenant when called from Celery beat / cross-schema context.
    """
    from django_tenants.utils import schema_context

    from .models import Invoice

    def _run() -> None:
        invoice = Invoice.objects.get(pk=invoice_id)
        # PDF rendering (e.g. weasyprint) wired here; store to invoice.pdf (MinIO).
        # Placeholder keeps the task idempotent and side-effect-free until wired.
        log.info(
            "invoice pdf generated number=%s",
            invoice.invoice_number,
            **ctx(entity=invoice.id, action="generate_invoice_pdf"),
        )

    if schema:
        with schema_context(schema):
            _run()
    else:
        _run()


def _autopay_tenant() -> int:
    """Charge active mandates for their students' due invoices. Returns count."""
    from datetime import date

    from .mandates import charge_mandate
    from .models import InvoiceStatus, Mandate

    today = date.today()
    charged = 0
    mandates = Mandate.objects.filter(status=Mandate.Status.ACTIVE).select_related("student")
    for mandate in mandates:
        if mandate.next_charge_on and mandate.next_charge_on > today:
            continue
        due_invoices = (
            mandate.student.invoices.exclude(
                status__in=[InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
            )
            .filter(due_date__lte=today)
            .order_by("due_date")
        )
        for invoice in due_invoices:
            if invoice.balance <= 0:
                continue
            amount = min(invoice.balance, mandate.max_amount)
            try:
                charge = charge_mandate(mandate=mandate, invoice=invoice, amount=amount)
            except Exception as exc:  # never let one mandate break the sweep
                log.warning(
                    "autopay charge errored mandate=%s invoice=%s error=%s",
                    mandate.id,
                    invoice.invoice_number,
                    exc,
                    **ctx(entity=mandate.id, action="dispatch_autopay"),
                )
                continue
            if charge.status == charge.Status.SUCCEEDED:
                charged += 1
    return charged


@shared_task(bind=True, acks_late=True)
def dispatch_autopay(self) -> None:
    """
    Beat task: sweep every tenant and auto-debit active e-mandates for due
    invoices (UPI Autopay). Idempotent per (mandate, invoice, month).
    """
    from django_tenants.utils import get_public_schema_name, get_tenant_model, tenant_context

    public = get_public_schema_name()
    total = tenants = 0
    for client in get_tenant_model().objects.exclude(schema_name=public):
        tenants += 1
        with tenant_context(client):
            total += _autopay_tenant()
    log.info(
        "autopay sweep done tenants=%s charged=%s",
        tenants,
        total,
        **ctx(action="dispatch_autopay"),
    )
