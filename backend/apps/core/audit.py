"""
Audit-trail helper (CLAUDE.md — user-facing "who changed what").

`record_audit` writes one immutable AuditLog row in the current tenant schema.
Call it from the service layer alongside the business action, passing the acting
user. It never raises — an audit hiccup must not roll back a money write — and it
also emits an `info` log so the same event lands in the server log stream (§9).
"""

from __future__ import annotations

from apps.core.logging import ctx, get_logger
from apps.core.models import AuditLog

log = get_logger("audit")


def _actor_label(actor) -> str:
    if not actor or not getattr(actor, "pk", None):
        return "system"
    return getattr(actor, "email", "") or getattr(actor, "get_username", lambda: "")() or "user"


def record_audit(
    *,
    action: str,
    entity=None,
    summary: str = "",
    changes: dict | None = None,
    actor=None,
    ip_address: str | None = None,
) -> AuditLog | None:
    """Persist an audit entry. Returns the row, or None if writing failed."""
    entity_type = entity.__class__.__name__ if entity is not None else ""
    entity_id = str(getattr(entity, "pk", "") or "") if entity is not None else ""
    try:
        entry = AuditLog.objects.create(
            actor=actor if getattr(actor, "pk", None) else None,
            actor_label=_actor_label(actor),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary[:255],
            changes=changes or {},
            ip_address=ip_address or None,
        )
    except Exception as exc:  # never let auditing break the operation
        log.warning(
            "audit write failed action=%s entity=%s error=%s",
            action,
            f"{entity_type}#{entity_id}",
            exc,
            **ctx(user=getattr(actor, "id", "-"), action="audit"),
        )
        return None

    log.info(
        "audit %s %s#%s",
        action,
        entity_type,
        entity_id,
        **ctx(user=getattr(actor, "id", "-"), entity=entity_id, action=action),
    )
    return entry
