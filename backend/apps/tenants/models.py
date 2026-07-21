"""
Tenant registry — lives ONLY in the public schema (CLAUDE.md §3).

`Client` is one school (= one PostgreSQL schema). `Domain` maps a hostname
(subdomain) to a client; TenantMainMiddleware resolves the request host to a
schema. Never store business data here.
"""

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Plan(models.Model):
    """A subscription plan (public schema). Defines price + per-tenant limits."""

    class Interval(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    name = models.CharField(max_length=60, unique=True)
    code = models.SlugField(max_length=40, unique=True, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTHLY)
    trial_days = models.PositiveIntegerField(default=0)
    max_students = models.PositiveIntegerField(default=0)  # 0 = unlimited
    features = models.JSONField(default=dict, blank=True)  # feature flags / module toggles
    is_active = models.BooleanField(default=True)
    # The plan new schools are placed on automatically (currently the Free plan).
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("price_monthly",)

    def __str__(self) -> str:
        return self.name

    @property
    def is_free(self) -> bool:
        return self.price_monthly == 0


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
    # Suspended schools stay provisioned but their staff cannot sign in.
    is_active = models.BooleanField(default=True)
    # Archived schools are read-only offboarding candidates (kept before delete).
    is_archived = models.BooleanField(default=False)
    plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients"
    )

    # django-tenants auto-creates the schema on save.
    auto_create_schema = True
    auto_drop_schema = False  # never silently drop a school's data

    def __str__(self) -> str:
        return self.name


class Domain(DomainMixin):
    pass


class BackupRun(models.Model):
    """
    A database backup + its verification outcome (CLAUDE.md §10 — backups are
    verified, not assumed). Platform-level, so it lives in the public schema
    (apps.tenants is SHARED). One row per pg_dump; `verified` flips true only
    after a successful restore-drill into a scratch database.
    """

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        VERIFIED = "verified", "Verified"
        FAILED = "failed", "Failed"

    label = models.CharField(max_length=120)
    path = models.CharField(max_length=500, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    table_count_total = models.BigIntegerField(default=0)  # summed rows across tables
    table_counts = models.JSONField(default=dict, blank=True)  # {"schema.table": n}
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    report = models.JSONField(default=dict, blank=True)
    error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Backup {self.label} [{self.status}]"
