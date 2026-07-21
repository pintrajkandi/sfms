"""Platform admin console — superuser-only + suspend enforcement (CLAUDE.md §3)."""

import time
from types import SimpleNamespace

import pytest
from django.http import HttpResponse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.tenants.admin_site import platform_admin

pytestmark = [pytest.mark.django_db]


def _req(**user_attrs):
    attrs = {"is_active": True, "is_superuser": False, **user_attrs}
    r = APIRequestFactory().get("/")
    r.user = SimpleNamespace(**attrs)
    return r


def test_admin_requires_superuser():
    # staff-but-not-superuser is rejected (master key → superuser only)
    assert platform_admin.has_permission(_req(is_superuser=False)) is False
    assert platform_admin.has_permission(_req(is_superuser=True)) is True
    assert platform_admin.has_permission(_req(is_active=False, is_superuser=True)) is False


def test_login_blocked_for_suspended_school():
    from apps.accounts.api import LoginView

    factory = APIRequestFactory()
    request = factory.post(
        "/api/v1/auth/login/",
        {"email": "admin@demo.test", "password": "whatever"},
        format="json",
    )
    request.tenant = SimpleNamespace(is_active=False, code=None)
    response = LoginView.as_view()(request)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["code"] == "school_suspended"


def test_client_admin_blocks_deletion():
    from apps.tenants.admin import ClientAdmin

    admin = ClientAdmin(
        model=__import__("apps.tenants.models", fromlist=["Client"]).Client,
        admin_site=platform_admin,
    )
    assert admin.has_delete_permission(_req(is_superuser=True)) is False


def test_tenant_apps_not_registered_on_platform_admin():
    # Only platform models are registered; tenant business models are absent.
    registered = {m.__name__ for m in platform_admin._registry}
    assert "Student" not in registered
    assert "Invoice" not in registered
    assert "Client" in registered
    assert "BackupRun" in registered


def test_reauth_freshness_window(settings):
    from apps.core.middleware import reauth_fresh

    settings.ADMIN_REAUTH_WINDOW = 600
    assert reauth_fresh(SimpleNamespace(session={"admin_auth_at": time.time()})) is True
    assert reauth_fresh(SimpleNamespace(session={"admin_auth_at": time.time() - 9999})) is False
    assert reauth_fresh(SimpleNamespace(session={})) is False


def test_admin_idle_timeout_logs_out(settings, monkeypatch):
    import apps.core.middleware as mw

    settings.ADMIN_SESSION_TIMEOUT = 1800
    settings.ADMIN_URL = "admin/"
    monkeypatch.setattr(mw, "logout", lambda request: None)  # avoid session.flush plumbing

    middleware = mw.AdminSessionTimeoutMiddleware(lambda r: HttpResponse("ok"))

    stale = SimpleNamespace(
        path="/admin/tenants/client/",
        user=SimpleNamespace(is_authenticated=True, id=1),
        session={"admin_last_seen": time.time() - 9999},
    )
    resp = middleware(stale)
    assert resp.status_code == 302  # bounced to login
    assert "login" in resp["Location"]

    fresh = SimpleNamespace(
        path="/admin/tenants/client/",
        user=SimpleNamespace(is_authenticated=True, id=1),
        session={"admin_last_seen": time.time()},
    )
    assert middleware(fresh).content == b"ok"  # passes through, activity refreshed
    assert "admin_last_seen" in fresh.session
