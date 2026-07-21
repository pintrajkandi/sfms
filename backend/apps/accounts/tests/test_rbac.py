"""Granular per-action RBAC policy + enforcement (CLAUDE.md §8)."""

import pytest

from apps.accounts.models import Role
from apps.accounts.permissions import RolePermission, allowed_roles, permissions_for

pytestmark = [pytest.mark.django_db]


class _View:
    def __init__(self, resource, action):
        self.rbac_resource = resource
        self.action = action


class _Req:
    def __init__(self, user, method="POST"):
        self.user = user
        self.method = method


class _User:
    is_authenticated = True

    def __init__(self, role):
        self.role = role


def _check(role, resource, action, method="POST"):
    return RolePermission().has_permission(_Req(_User(role), method), _View(resource, action))


def test_admin_allowed_everywhere():
    assert _check(Role.ADMIN, "settings", "update")
    assert _check(Role.ADMIN, "payouts", "create")


def test_finance_can_write_fees_staff_cannot():
    assert _check(Role.FINANCE, "fee-plans", "create")
    assert not _check(Role.STAFF, "fee-plans", "create")


def test_everyone_can_read():
    for role in (Role.STAFF, Role.FRONT_DESK, Role.HOD, Role.FINANCE):
        assert _check(role, "payments", "list", method="GET")


def test_only_admin_writes_settings():
    assert not _check(Role.FINANCE, "settings", "update")
    assert not _check(Role.HOD, "settings", "partial_update")
    assert _check(Role.ADMIN, "settings", "update")


def test_action_override_refund_is_finance_only():
    assert _check(Role.FINANCE, "invoices", "refund")
    # front_desk can create invoices but NOT refund (action override)
    assert _check(Role.FRONT_DESK, "invoices", "create")
    assert not _check(Role.FRONT_DESK, "invoices", "refund")


def test_bounce_is_finance_only():
    assert _check(Role.FINANCE, "payments", "bounce")
    assert not _check(Role.FRONT_DESK, "payments", "bounce")


def test_delete_is_admin_only():
    assert not _check(Role.FINANCE, "payments", "destroy")
    assert _check(Role.ADMIN, "payments", "destroy")


def test_unknown_resource_is_open():
    assert allowed_roles("not-a-resource", "create", "POST")  # returns ALL


def test_view_without_rbac_resource_is_allowed():
    class Bare:
        action = "create"

    assert RolePermission().has_permission(_Req(_User(Role.STAFF)), Bare()) is True


def test_permissions_map_for_frontend():
    perms = permissions_for(Role.FRONT_DESK)
    assert perms["invoices"]["write"] is True
    assert perms["invoices"]["delete"] is False
    assert perms["settings"]["write"] is False
    admin = permissions_for(Role.ADMIN)
    assert all(v["write"] and v["delete"] for v in admin.values())
