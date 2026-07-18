"""Read-only audit-trail API — the in-app 'who changed what' view."""

from __future__ import annotations

from rest_framework import serializers, viewsets

from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = (
            "id",
            "created_at",
            "actor",
            "actor_label",
            "action",
            "entity_type",
            "entity_id",
            "summary",
            "changes",
        )
        read_only_fields = fields


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Immutable audit log. Filter with ?entity_type=Invoice&entity_id=12,
    ?action=payment.recorded, or ?actor=<user id>.
    """

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        params = self.request.query_params
        if entity_type := params.get("entity_type"):
            qs = qs.filter(entity_type=entity_type)
        if entity_id := params.get("entity_id"):
            qs = qs.filter(entity_id=str(entity_id))
        if action := params.get("action"):
            qs = qs.filter(action=action)
        if actor := params.get("actor"):
            qs = qs.filter(actor_id=actor)
        return qs
