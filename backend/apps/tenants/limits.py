"""Per-tenant plan limits (billing). Read the plan from the public schema."""

from __future__ import annotations

from django.db import connection
from django_tenants.utils import get_public_schema_name, schema_context


def student_limit_for_current_tenant() -> int:
    """
    Max students allowed by the current school's plan (0 = unlimited). The Client
    is loaded by TenantMainMiddleware; the Plan lives in the public schema.
    """
    client = getattr(connection, "tenant", None)
    plan_id = getattr(client, "plan_id", None)
    if not plan_id:
        return 0
    try:
        with schema_context(get_public_schema_name()):
            from .models import Plan

            plan = Plan.objects.filter(pk=plan_id).first()
            return plan.max_students if plan else 0
    except Exception:
        return 0  # never block enrolment on a plan-lookup hiccup
