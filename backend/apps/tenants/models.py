"""
Tenant registry — lives ONLY in the public schema (CLAUDE.md §3).

`Client` is one school (= one PostgreSQL schema). `Domain` maps a hostname
(subdomain) to a client; TenantMainMiddleware resolves the request host to a
schema. Never store business data here.
"""

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    name = models.CharField(max_length=200)

    # Login identity: `slug` is the subdomain (greenfield-high.feeledger.app);
    # `code` is the human school code used on the sign-in screen (e.g. GHPS-2847).
    # null (not "") for unset, so multiple non-onboarded tenants (public, demo)
    # don't collide on the unique constraint.
    slug = models.SlugField(max_length=63, unique=True, null=True, blank=True)
    code = models.CharField(max_length=16, unique=True, null=True, blank=True)

    # Provisioning metadata (not business data).
    on_trial = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    created_on = models.DateField(auto_now_add=True)

    # django-tenants auto-creates the schema on save.
    auto_create_schema = True
    auto_drop_schema = False  # never silently drop a school's data

    def __str__(self) -> str:
        return self.name


class Domain(DomainMixin):
    pass
