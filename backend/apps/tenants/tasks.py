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


@shared_task(bind=True, acks_late=True)
def backup_school(self, schema_name: str) -> None:
    """Back up one school's schema to object storage. Runs in the public schema."""
    from django_tenants.utils import get_public_schema_name

    from .backups import create_schema_backup
    from .models import Client

    client = Client.objects.filter(schema_name=schema_name).first()
    if client is None or client.schema_name == get_public_schema_name():
        return
    run = create_schema_backup(client=client, label="daily")
    log.info(
        "school backup done schema=%s size=%s",
        schema_name,
        run.size_bytes,
        **ctx(entity=run.id, action="backup_school"),
    )


@shared_task(bind=True, acks_late=True)
def nightly_school_backups(self) -> None:
    """Fan out a daily per-school backup for every active tenant schema."""
    from django_tenants.utils import get_public_schema_name

    from .models import Client

    schemas = (
        Client.objects.exclude(schema_name=get_public_schema_name())
        .filter(is_active=True)
        .values_list("schema_name", flat=True)
    )
    n = 0
    for schema in schemas:
        backup_school.delay(schema)
        n += 1
    log.info("queued %s per-school backups", n, **ctx(action="nightly_school_backups"))
