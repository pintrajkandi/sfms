"""
Platform admin site (public schema only) — the master console.

This is a *root account*: it can reach every school's registry + provisioning.
So it is superuser-only (not merely is_staff), branded distinctly so operators
know they're in the platform console, and it hosts the tenant registry + backup
records. Tenant business data is NOT here — schools use the app UI (CLAUDE.md §3).

Adds a cross-tenant dashboard (the index) and an ops-health panel.
"""

from __future__ import annotations

from django.template.response import TemplateResponse
from django.urls import path
from unfold.sites import UnfoldAdminSite


class PlatformAdminSite(UnfoldAdminSite):
    site_header = "YukiCares — Platform Console"
    site_title = "YukiCares Platform"
    index_title = "Schools, domains & platform operations"

    def has_permission(self, request) -> bool:
        # Master key to every tenant → superuser-only, not just is_staff.
        user = request.user
        return bool(user.is_active and user.is_superuser)

    # --- Dashboard: cross-tenant totals on the index page ---
    def index(self, request, extra_context=None):
        from .platform_stats import platform_stats

        extra_context = extra_context or {}
        try:
            extra_context["platform_stats"] = platform_stats()
        except Exception:
            extra_context["platform_stats"] = None
        return super().index(request, extra_context)

    # --- Ops panel + tenant support console ---
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("ops/", self.admin_view(self.ops_view), name="ops"),
            path("support/", self.admin_view(self.support_index), name="support"),
            path(
                "support/<str:schema>/", self.admin_view(self.support_detail), name="support-detail"
            ),
        ]
        return custom + urls

    def ops_view(self, request):
        from .ops import ops_health

        context = {
            **self.each_context(request),
            "title": "Ops health",
            "health": ops_health(),
        }
        return TemplateResponse(request, "admin/ops.html", context)

    def support_index(self, request):
        """Pick a school to inspect (read-only support browse)."""
        from django_tenants.utils import get_public_schema_name

        from .models import Client

        clients = Client.objects.exclude(schema_name=get_public_schema_name()).order_by("name")
        context = {**self.each_context(request), "title": "Tenant support", "clients": clients}
        return TemplateResponse(request, "admin/support_index.html", context)

    def support_detail(self, request, schema):
        """Read-only view of one school's data, inside its schema."""
        from django.http import Http404
        from django_tenants.utils import tenant_context

        from .models import Client
        from .support import gather_support_data

        client = Client.objects.filter(schema_name=schema).first()
        if client is None:
            raise Http404("School not found.")
        with tenant_context(client):
            data = gather_support_data()
        context = {
            **self.each_context(request),
            "title": f"Support · {client.name}",
            "client": client,
            "data": data,
        }
        return TemplateResponse(request, "admin/support_detail.html", context)


# Single instance mounted in config/urls_public.py at settings.ADMIN_URL.
platform_admin = PlatformAdminSite(name="platform_admin")
