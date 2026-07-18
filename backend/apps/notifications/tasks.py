"""
Email dispatch via Celery (MSG91 SMTP relay in prod, console in dev).

Tasks are idempotent and take primitives (address/subject/body), not objects —
sending is tenant-agnostic once the message is rendered, so no schema switch is
needed here (CLAUDE.md §5).
"""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from apps.core.logging import ctx, get_logger

log = get_logger("notifications.tasks")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    acks_late=True,
)
def send_email(self, to_email: str, subject: str, body: str, html_body: str | None = None) -> None:
    # Domain only — never log the full recipient / body (PII).
    domain = to_email.rsplit("@", 1)[-1] if "@" in to_email else "-"
    log.info(
        "email sending via %s subject=%r to_domain=%s attempt=%s",
        settings.EMAIL_HOST,
        subject,
        domain,
        self.request.retries + 1,
        **ctx(action="send_email"),
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    if html_body:
        message.attach_alternative(html_body, "text/html")
    try:
        sent = message.send()
    except Exception as exc:
        # Loud, structured failure in the worker logs (e.g. MSG91 SMTP rejection).
        log.error(
            "email send FAILED subject=%r to_domain=%s host=%s error=%s",
            subject,
            domain,
            settings.EMAIL_HOST,
            exc,
            **ctx(action="send_email"),
        )
        raise
    log.info(
        "email sent subject=%r to_domain=%s delivered=%s",
        subject,
        domain,
        sent,
        **ctx(action="send_email"),
    )
