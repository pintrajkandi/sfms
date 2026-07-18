"""Thin façade over the async email task so callers don't import Celery directly."""

from __future__ import annotations


def send_mail_async(
    *, to_email: str, subject: str, body: str, html_body: str | None = None
) -> None:
    # Imported lazily to keep apps.core import-light.
    from apps.notifications.tasks import send_email

    send_email.delay(to_email, subject, body, html_body)
