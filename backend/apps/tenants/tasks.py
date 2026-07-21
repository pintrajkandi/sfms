"""Platform ops tasks — nightly verified backup (CLAUDE.md §10)."""

from __future__ import annotations

from celery import shared_task

from apps.core.logging import ctx, get_logger

log = get_logger("tenants.tasks")


@shared_task(bind=True, acks_late=True)
def nightly_backup(self) -> None:
    """Create a verified backup + restore drill. Runs in the public schema."""
    from .backups import create_backup, verify_backup

    try:
        run = create_backup(label="nightly")
        run = verify_backup(run)
        log.info(
            "nightly backup done label=%s verified=%s",
            run.label,
            run.verified,
            **ctx(entity=run.id, action="nightly_backup"),
        )
    except Exception as exc:
        log.error("nightly backup failed error=%s", exc, **ctx(action="nightly_backup"))
        raise
