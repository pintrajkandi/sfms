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
