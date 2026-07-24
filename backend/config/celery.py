"""Celery app — RabbitMQ broker, Redis result backend."""

import os

from celery import Celery
from celery.schedules import crontab

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
    # UPI Autopay: auto-debit active e-mandates for due invoices (idempotent).
    "dispatch-autopay": {
        "task": "apps.collections.tasks.dispatch_autopay",
        "schedule": 60 * 60 * 24.0,  # once daily
    },
    # Nightly verified DB backup + restore drill (backups are verified, not assumed).
    # Fixed clock time so ops know exactly when the maintenance window runs.
    "nightly-backup": {
        "task": "apps.tenants.tasks.nightly_backup",
        "schedule": crontab(hour=2, minute=0),  # 02:00 daily (whole-cluster)
    },
    # Daily per-school schema backup to object storage (downloadable/restorable
    # from the platform admin). Staggered after the whole-cluster job so they
    # don't contend for the DB at the same instant.
    "nightly-school-backups": {
        "task": "apps.tenants.tasks.nightly_school_backups",
        "schedule": crontab(hour=3, minute=0),  # 03:00 daily (per-school)
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self) -> None:  # pragma: no cover
    print(f"Request: {self.request!r}")
