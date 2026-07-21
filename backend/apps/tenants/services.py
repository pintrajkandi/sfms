"""
School onboarding / provisioning (public schema only).

`provision_school` is the single source of truth for creating a tenant: it
generates a unique subdomain slug + school code, creates the schema + domain, and
seeds the first admin user inside the tenant schema. The `provision_tenant`
management command and the public signup API both call this.
"""

from __future__ import annotations

import re
import secrets
import string

from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from django_tenants.utils import schema_context

from apps.core.logging import ctx, get_logger

log = get_logger("provisioning")

# Base domain staff sign in from. Overridable per environment (dev uses .localhost).
TENANT_BASE_DOMAIN = getattr(settings, "TENANT_BASE_DOMAIN", "localhost")

_RESERVED_SLUGS = {"www", "app", "api", "admin", "public", "static", "media"}


def normalize_slug(raw: str) -> str:
    slug = slugify(raw)[:63].strip("-")
    return slug


def slug_available(slug: str) -> bool:
    from apps.tenants.models import Client

    if not slug or slug in _RESERVED_SLUGS or not re.fullmatch(r"[a-z0-9-]{2,63}", slug):
        return False
    return not Client.objects.filter(slug=slug).exists()


def _unique_slug(base: str) -> str:
    from apps.tenants.models import Client

    slug = normalize_slug(base) or "school"
    candidate = slug
    i = 2
    while candidate in _RESERVED_SLUGS or Client.objects.filter(slug=candidate).exists():
        candidate = f"{slug}-{i}"
        i += 1
    return candidate


def ensure_free_plan():
    """The default plan every new school is placed on. Free + unlimited for now.

    Paid plans can be added later (via admin); whichever plan has is_default=True
    is the one new tenants receive.
    """
    from apps.tenants.models import Plan

    plan, _ = Plan.objects.get_or_create(
        code="free",
        defaults={
            "name": "Free",
            "description": "All features included. Paid plans coming soon.",
            "price_monthly": 0,
            "max_students": 0,  # unlimited
            "is_default": True,
            "is_active": True,
        },
    )
    return plan


def default_plan():
    """The plan new tenants get: the flagged default, else the free plan."""
    from apps.tenants.models import Plan

    return Plan.objects.filter(is_default=True, is_active=True).first() or ensure_free_plan()


def subscription_status(tenant, *, student_count: int = 0) -> dict:
    """Current subscription for a tenant. Everyone is on the free plan for now."""
    plan = getattr(tenant, "plan", None) or default_plan()
    max_students = plan.max_students or 0
    return {
        "plan": {
            "name": plan.name,
            "code": plan.code,
            "description": plan.description,
            "price_monthly": str(plan.price_monthly),
            "currency": plan.currency,
            "interval": plan.interval,
            "is_free": plan.is_free,
            "features": plan.features or {},
        },
        "status": "active",
        "is_free": plan.is_free,
        "on_trial": getattr(tenant, "on_trial", False),
        "renews_at": tenant.paid_until.isoformat() if getattr(tenant, "paid_until", None) else None,
        "student_count": student_count,
        "max_students": max_students,  # 0 = unlimited
        "student_limit_reached": bool(max_students) and student_count >= max_students,
    }


def _generate_code(name: str) -> str:
    from apps.tenants.models import Client

    # Prefix from initials (e.g. "Greenfield High Public School" -> "GHPS").
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", name))[:4].upper() or "SCH"
    while True:
        suffix = "".join(secrets.choice(string.digits) for _ in range(4))
        code = f"{initials}-{suffix}"
        if not Client.objects.filter(code=code).exists():
            return code


@transaction.atomic
def provision_school(
    *,
    name: str,
    admin_full_name: str,
    admin_email: str,
    admin_password: str,
    slug: str | None = None,
    schema_name: str | None = None,
):
    """Create a school tenant + first admin. Returns the Client. Public schema only."""
    from apps.accounts.models import Role, User
    from apps.tenants.models import Client, Domain

    final_slug = _unique_slug(slug or name)
    final_schema = schema_name or final_slug.replace("-", "_")
    code = _generate_code(name)

    plan = default_plan()
    client = Client(
        schema_name=final_schema,
        name=name,
        slug=final_slug,
        code=code,
        plan=plan,
        on_trial=False,  # free plan — not a time-limited trial
    )
    client.save()  # auto-creates + migrates the schema

    domain = f"{final_slug}.{TENANT_BASE_DOMAIN}"
    Domain.objects.create(domain=domain, tenant=client, is_primary=True)

    first, _, last = admin_full_name.partition(" ")
    with schema_context(final_schema):
        admin = User.objects.create_superuser(
            username=admin_email,
            email=admin_email,
            password=admin_password,
            first_name=first,
            last_name=last,
            role=Role.ADMIN,
            email_verified=False,  # must click the verification link before signing in
        )
        from apps.accounts.services import send_verification_email

        send_verification_email(admin, school_name=name, slug=final_slug)

        # Seed starter departments/classes/sections (admin can keep or delete).
        from apps.schools.seed import seed_default_setup

        seed_default_setup()

    log.info(
        "school provisioned slug=%s code=%s domain=%s",
        final_slug,
        code,
        domain,
        **ctx(entity=final_schema, action="provision_school"),
    )
    return client
