"""
Payment-receipt WhatsApp on Payment creation.

Connected in NotificationsConfig.ready(). EVERYTHING is wrapped in try/except and
failures log at `warn` — recording a payment must NEVER break because messaging
misfired (CLAUDE.md §9). Runs inside the tenant schema the payment was saved in,
so the receiver reaches the correct student/school data with no schema switch.
"""

from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.logging import ctx, get_logger

log = get_logger("notifications.signals")


@receiver(post_save, dispatch_uid="notifications.payment_receipt")
def send_payment_receipt(sender, instance, created, **kwargs) -> None:
    # Late import + label check keeps this from importing collections at app load
    # and avoids reacting to unrelated models sharing the signal.
    if sender._meta.label != "collections.Payment":
        return
    if not created:
        return

    try:
        from apps.schools.models import SchoolSettings

        from .messaging import notify

        student = instance.invoice.student
        phone = getattr(student, "guardian_phone", "")
        if not phone:
            return

        guardian = student.guardian_name or "Guardian"
        school = SchoolSettings.objects.values_list("name", flat=True).first() or "your school"
        invoice = instance.invoice
        message = (
            f"Dear {guardian}, we received {instance.amount} {instance.currency} for "
            f"{student.full_name} (receipt {invoice.invoice_number}). "
            f"Outstanding balance: {invoice.balance} {invoice.currency}. — {school}"
        )
        notify(phone, message, whatsapp=True, sms=True)
        log.info(
            "payment receipt queued invoice=%s",
            invoice.invoice_number,
            **ctx(entity=instance.pk, action="payment_receipt"),
        )
    except Exception as exc:
        # Never let a messaging hiccup roll back / crash the payment.
        log.warning(
            "payment receipt skipped payment=%s error=%s",
            getattr(instance, "pk", "-"),
            exc,
            **ctx(entity=getattr(instance, "pk", "-"), action="payment_receipt"),
        )


@receiver(post_save, dispatch_uid="notifications.invoice_generated")
def send_invoice_generated(sender, instance, created, **kwargs) -> None:
    # Late import + label check keeps this from importing collections at app load
    # and avoids reacting to unrelated models sharing the signal.
    if sender._meta.label != "collections.Invoice":
        return
    # NOTE: we do NOT fire on `created`. create_invoice() inserts the row as an
    # empty DRAFT (total 0) and only fills lines/totals on a follow-up save, so
    # the create signal would announce "Amount: 0.00". Fire when the invoice is
    # finalized (non-draft, non-cancelled) and dedupe so it goes out exactly once.
    from apps.collections.models import InvoiceStatus

    if instance.status in (InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED):
        return

    from django.core.cache import cache

    # cache.add succeeds only the first time — every later save (e.g. a payment
    # updating amount_paid) is a no-op. Key is tenant-scoped by our key function.
    if not cache.add(f"invoice_gen_notified:{instance.pk}", 1, 90 * 86400):
        return

    try:
        from .messaging import notify

        student = instance.student
        phone = getattr(student, "guardian_phone", "")
        if not phone:
            return

        guardian = student.guardian_name or "Guardian"
        due = f"{instance.due_date:%d %b %Y}" if instance.due_date else "soon"
        message = (
            f"Dear {guardian}, invoice {instance.invoice_number} for "
            f"{student.full_name} has been generated. "
            f"Amount: {instance.total} {instance.currency}, due {due}. "
            f"Log in to the parent portal to pay."
        )
        notify(phone, message)
        log.info(
            "invoice generated notice queued invoice=%s",
            instance.invoice_number,
            **ctx(entity=instance.pk, action="invoice_generated"),
        )
    except Exception as exc:
        # Never let a messaging hiccup roll back / crash invoice creation.
        log.warning(
            "invoice generated notice skipped invoice=%s error=%s",
            getattr(instance, "pk", "-"),
            exc,
            **ctx(entity=getattr(instance, "pk", "-"), action="invoice_generated"),
        )
