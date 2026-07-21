"""Platform-operator features: dashboard, impersonation, ops, offboarding, limits."""

import json

import pytest
from django.core import signing
from rest_framework.test import APIRequestFactory

pytestmark = [pytest.mark.django_db]


# --- platform dashboard stats ---
def test_platform_stats_shape(tenant_ctx):
    from apps.tenants.platform_stats import invalidate, platform_stats

    invalidate()
    s = platform_stats(use_cache=False)
    assert {
        "schools_total",
        "schools_active",
        "students_total",
        "verification_pending",
        "mrr",
    } <= set(s)
    assert isinstance(s["schools_total"], int)


# --- ops health ---
def test_ops_health_rows():
    from apps.tenants.ops import ops_health

    rows = ops_health()
    names = {r["name"] for r in rows}
    assert "PostgreSQL" in names
    assert all("ok" in r and "detail" in r for r in rows)


# --- impersonation tickets ---
def test_ticket_round_trip():
    from apps.tenants.impersonation import make_ticket, read_ticket

    op = type("U", (), {"pk": 1, "email": "op@platform.test"})()
    token = make_ticket(operator=op, target_user_id=42, schema="demo")
    data = read_ticket(token)
    assert data["uid"] == 42 and data["schema"] == "demo" and data["op_email"] == "op@platform.test"


def test_ticket_expired():
    from apps.tenants.impersonation import make_ticket, read_ticket

    op = type("U", (), {"pk": 1, "email": "op@x"})()
    token = make_ticket(operator=op, target_user_id=1, schema="demo")
    with pytest.raises(signing.SignatureExpired):
        read_ticket(token, max_age=-1)


def test_impersonate_view_rejects_bad_ticket(tenant_ctx):
    from apps.accounts.api import ImpersonateView

    req = APIRequestFactory().post(
        "/api/v1/auth/impersonate/", {"ticket": "garbage"}, format="json"
    )
    resp = ImpersonateView.as_view()(req)
    assert resp.status_code == 403


def test_impersonate_view_rejects_wrong_schema(tenant_ctx):
    from apps.accounts.api import ImpersonateView
    from apps.tenants.impersonation import make_ticket

    op = type("U", (), {"pk": 1, "email": "op@x"})()
    ticket = make_ticket(operator=op, target_user_id=1, schema="some_other_schema")
    req = APIRequestFactory().post("/api/v1/auth/impersonate/", {"ticket": ticket}, format="json")
    resp = ImpersonateView.as_view()(req)
    assert resp.status_code == 403


# --- offboarding / export ---
def test_export_tenant_json(tenant_ctx):
    from apps.students.services import create_student
    from apps.tenants.models import Client
    from apps.tenants.offboarding import export_tenant_json

    create_student(first_name="Exp", last_name="Ort")
    client = Client.objects.get(schema_name="test")
    payload = export_tenant_json(client)
    parsed = json.loads(payload)
    assert isinstance(parsed, list)
    assert any(row["model"] == "students.student" for row in parsed)


def test_delete_tenant_requires_archived(tenant_ctx):
    from apps.core.services import ServiceError
    from apps.tenants.models import Client
    from apps.tenants.offboarding import delete_tenant

    client = Client.objects.get(schema_name="test")
    client.is_archived = False
    with pytest.raises(ServiceError):
        delete_tenant(client)


# --- billing limits ---
def test_student_limit_unlimited_without_plan(tenant_ctx):
    from apps.tenants.limits import student_limit_for_current_tenant

    assert student_limit_for_current_tenant() == 0  # no connection.tenant/plan → unlimited


# --- support console data ---
def test_gather_support_data(tenant_ctx):
    from apps.students.services import create_student
    from apps.tenants.support import gather_support_data

    create_student(first_name="Sup", last_name="Port")
    data = gather_support_data()
    assert data["counts"]["students"] >= 1
    assert "payouts" in data and "staff" in data
