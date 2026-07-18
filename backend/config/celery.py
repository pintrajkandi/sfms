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
}


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover
    print(f"Request: {self.request!r}")
