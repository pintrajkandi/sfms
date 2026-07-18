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

    client = Client(schema_name=final_schema, name=name, slug=final_slug, code=code)
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

    log.info(
        "school provisioned slug=%s code=%s domain=%s",
        final_slug,
        code,
        domain,
        **ctx(entity=final_schema, action="provision_school"),
    )
    return client
