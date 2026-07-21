"""
Create the public tenant + its domain so the platform (admin/health) is reachable.

django-tenants resolves every request host to a schema; the public schema needs
its own Client + Domain row. The public schema itself already exists (migrated),
and django-tenants special-cases it so it is not recreated.

    python manage.py bootstrap_public --domain localhost
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django_tenants.utils import get_public_schema_name

from apps.core.logging import ctx, get_logger

log = get_logger("provisioning")


class Command(BaseCommand):
    help = "Create the public tenant and its domain (idempotent)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--domain", default="localhost")

    def handle(self, *args, **opts) -> None:
        from apps.tenants.models import Client, Domain

        public_schema = get_public_schema_name()
        client, created = Client.objects.get_or_create(
            schema_name=public_schema, defaults={"name": "Public"}
        )
        Domain.objects.get_or_create(
            domain=opts["domain"], tenant=client, defaults={"is_primary": True}
        )
        from apps.tenants.services import ensure_free_plan

        ensure_free_plan()
        log.info(
            "public tenant ready domain=%s",
            opts["domain"],
            **ctx(entity=public_schema, action="bootstrap_public"),
        )
        msg = "created" if created else "already present"
        self.stdout.write(self.style.SUCCESS(f"Public tenant {msg}; domain {opts['domain']}"))
