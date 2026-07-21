"""Seed default departments/classes/sections into an existing tenant schema.

New schools get this automatically at onboarding (see apps.tenants.services.
provision_school). Use this to backfill a school that was created earlier.

    python manage.py seed_defaults --schema <schema_name>
    python manage.py seed_defaults --all        # every non-public tenant
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context

from apps.schools.seed import seed_default_setup


class Command(BaseCommand):
    help = "Seed default departments/classes/sections into a tenant schema (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--schema", help="Target tenant schema name.")
        parser.add_argument(
            "--all", action="store_true", help="Seed every non-public tenant schema."
        )

    def handle(self, *args, **opts):
        from apps.tenants.models import Client

        if opts["all"]:
            schemas = list(
                Client.objects.exclude(schema_name="public").values_list("schema_name", flat=True)
            )
        elif opts.get("schema"):
            schemas = [opts["schema"]]
        else:
            raise CommandError("Provide --schema <name> or --all.")

        for schema in schemas:
            with schema_context(schema):
                summary = seed_default_setup()
            self.stdout.write(self.style.SUCCESS(f"{schema}: seeded {summary}"))
