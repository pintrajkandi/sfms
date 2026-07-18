"""Celery app — RabbitMQ broker, Redis result backend."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("sfms")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Recurring background work (Celery beat).
app.conf.beat_schedule = {
    # Keep (re)sending verification emails to unverified users until they verify.
    "dispatch-pending-verifications": {
        "task": "apps.accounts.tasks.dispatch_pending_verifications",
        "schedule": 60 * 60.0,  # hourly sweep (per-user cooldown prevents spam)
    },
    # Staged fee reminders (T-7 / T-3 / due / overdue). Runs daily so each stage
    # is caught as an invoice reaches it; per-stage cache gates prevent re-sends.
    "dispatch-fee-reminders": {
        "task": "apps.notifications.tasks.dispatch_fee_reminders",
        "schedule": 60 * 60 * 24.0,  # once daily
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover
    print(f"Request: {self.request!r}")
