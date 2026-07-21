"""
Granular, per-action RBAC (CLAUDE.md — roles exist; this adds enforcement).

A central POLICY maps each resource to the roles allowed to read / write / delete
it, with optional per-action overrides (e.g. only finance may refund). Viewsets
opt in by setting `rbac_resource`; anything without one is unrestricted (still
behind IsAuthenticated). School Admin is allowed everywhere. The same matrix is
surfaced to the frontend via /auth/me/ so the UI can hide forbidden actions.
"""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from .models import Role

ALL = {Role.ADMIN, Role.FINANCE, Role.HOD, Role.STAFF, Role.FRONT_DESK}
FINANCE = {Role.ADMIN, Role.FINANCE}
FRONT = {Role.ADMIN, Role.FINANCE, Role.FRONT_DESK}
ADMIN_ONLY = {Role.ADMIN}

# resource -> {read, write, delete, actions: {action_name: roles}}
POLICY: dict[str, dict] = {
    "invoices": {
        "read": ALL,
        "write": FRONT,
        "delete": ADMIN_ONLY,
        "actions": {
            "refund": FINANCE,
            "credit_note": FINANCE,
            "einvoice": FINANCE,
            "payment_plan": FRONT,
        },
    },
    "payments": {
        "read": ALL,
        "write": FRONT,
        "delete": ADMIN_ONLY,
        "actions": {"bounce": FINANCE},
    },
    "bank-statements": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "mandates": {
        "read": ALL,
        "write": FRONT,
        "delete": ADMIN_ONLY,
        "actions": {"charge": FINANCE, "cancel": FINANCE, "activate": FINANCE},
    },
    "payouts": {
        "read": ALL,
        "write": {Role.ADMIN, Role.FINANCE, Role.HOD},
        "delete": ADMIN_ONLY,
        "actions": {
            "transition": {Role.ADMIN, Role.FINANCE, Role.HOD},
            "payroll": FINANCE,
        },
    },
    "teachers": {"read": ALL, "write": {Role.ADMIN, Role.HOD}, "delete": ADMIN_ONLY},
    "discount-rules": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "student-discounts": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "fee-plans": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "fee-types": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "fee-categories": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "expenses": {
        "read": ALL,
        "write": {Role.ADMIN, Role.FINANCE, Role.STAFF},
        "delete": ADMIN_ONLY,
    },
    "ledger": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "accounts": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "journal": {"read": ALL, "write": FINANCE, "delete": ADMIN_ONLY},
    "inventory": {"read": ALL, "write": {Role.ADMIN, Role.STAFF}, "delete": ADMIN_ONLY},
    "transport": {
        "read": ALL,
        "write": {Role.ADMIN, Role.STAFF, Role.FINANCE},
        "delete": ADMIN_ONLY,
    },
    "students": {"read": ALL, "write": FRONT, "delete": ADMIN_ONLY},
    "settings": {"read": ALL, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "academic-years": {"read": ALL, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "classes": {"read": ALL, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "departments": {"read": ALL, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "support": {"read": ALL, "write": ALL, "delete": ADMIN_ONLY},
    "audit-logs": {"read": ALL, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    # Data privacy — export/erasure and the consent ledger are admin-only.
    "privacy": {"read": ADMIN_ONLY, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "consents": {"read": ALL, "write": FRONT, "delete": ADMIN_ONLY},
    "data-requests": {"read": ADMIN_ONLY, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    "backups": {"read": ADMIN_ONLY, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
    # Staff/team management — admin-only.
    "team": {"read": ADMIN_ONLY, "write": ADMIN_ONLY, "delete": ADMIN_ONLY},
}

# DRF action -> permission group.
_READ_ACTIONS = {"list", "retrieve"}
_WRITE_ACTIONS = {"create", "update", "partial_update"}
_DELETE_ACTIONS = {"destroy"}
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _group_for(action: str, method: str) -> str:
    if action in _READ_ACTIONS or (action is None and method in _SAFE_METHODS):
        return "read"
    if action in _DELETE_ACTIONS:
        return "delete"
    return "write"


def allowed_roles(resource: str, action: str, method: str) -> set:
    policy = POLICY.get(resource)
    if policy is None:
        return ALL
    overrides = policy.get("actions", {})
    if action in overrides:
        return overrides[action]
    return policy.get(_group_for(action, method), ALL)


class RolePermission(BasePermission):
    """Enforce POLICY for any view that declares `rbac_resource`."""

    message = "Your role is not permitted to perform this action."

    def has_permission(self, request, view) -> bool:
        resource = getattr(view, "rbac_resource", None)
        if resource is None:
            return True  # not an RBAC-guarded resource
        user = request.user
        if not (user and user.is_authenticated):
            return False
        role = getattr(user, "role", None)
        if role == Role.ADMIN:
            return True
        action = getattr(view, "action", None)
        return role in allowed_roles(resource, action, request.method)


def permissions_for(role: str) -> dict:
    """Effective {resource: {read, write, delete}} map for the frontend."""
    out = {}
    for resource, policy in POLICY.items():
        out[resource] = {
            "read": role == Role.ADMIN or role in policy.get("read", ALL),
            "write": role == Role.ADMIN or role in policy.get("write", ALL),
            "delete": role == Role.ADMIN or role in policy.get("delete", ALL),
        }
    return out
