"""
Tenant offboarding — full-tenant data export + the suspend→archive→delete flow.

`export_tenant_json` dumps every business record in a school's schema (GDPR at
the tenant level). Deletion is intentionally hard: only an archived school can be
dropped, and the caller must force it — the schema is real data.
"""

from __future__ import annotations

from django.apps import apps as django_apps
from django.core import serializers
from django_tenants.utils import tenant_context

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger

log = get_logger("tenants.offboarding")

# Apps whose models live in the tenant schema (mirror settings.TENANT_APPS).
_TENANT_APP_LABELS = {
    "accounts",
    "core",
    "schools",
    "students",
    "fees",
    "collections",
    "staff",
    "expenses",
    "inventory",
    "finance",
    "notifications",
    "portal",
    "privacy",
}


def export_tenant_json(client) -> str:
    """Serialize every tenant-app record in the school's schema to JSON."""
    with tenant_context(client):
        objs = []
        for model in django_apps.get_models():
            if model._meta.abstract or model._meta.app_label not in _TENANT_APP_LABELS:
                continue
            try:
                objs.extend(model.objects.all())
            except Exception:
                continue  # model not in this schema — skip
        payload = serializers.serialize("json", objs, indent=2)
    log.info(
        "tenant exported schema=%s objects=%s",
        client.schema_name,
        len(objs),
        **ctx(entity=client.schema_name, action="export_tenant"),
    )
    return payload


def archive_tenant(client, *, actor=None) -> None:
    """Suspend + archive a school (read-only offboarding state)."""
    client.is_active = False
    client.is_archived = True
    client.save(update_fields=["is_active", "is_archived"])
    log.warning(
        "tenant archived schema=%s",
        client.schema_name,
        **ctx(user=getattr(actor, "id", "-"), entity=client.schema_name, action="archive_tenant"),
    )
    record_audit(
        action="tenant.archived", entity=None, summary=f"Archived school {client.name}", actor=actor
    )


def delete_tenant(client, *, actor=None) -> None:
    """
    Permanently drop an ARCHIVED school (schema + registry). Irreversible — the
    caller is responsible for the guardrails (archived-only, re-auth, confirm).
    """
    if not client.is_archived:
        from apps.core.services import ServiceError

        raise ServiceError("Only archived schools can be deleted.")
    name, schema = client.name, client.schema_name
    client.delete(force_drop=True)  # django-tenants drops the schema
    log.error(
        "tenant deleted schema=%s (schema dropped)",
        schema,
        **ctx(user=getattr(actor, "id", "-"), entity=schema, action="delete_tenant"),
    )
    record_audit(
        action="tenant.deleted",
        entity=None,
        summary=f"Deleted school {name} ({schema})",
        actor=actor,
    )
