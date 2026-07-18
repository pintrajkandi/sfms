"""
Provision a school (tenant): creates the schema, a domain, and an admin user.

Named `provision_tenant` to avoid colliding with django-tenants' own
`create_tenant` command.

    python manage.py provision_tenant \
        --schema demo --name "Demo School" --domain demo.localhost \
        --admin-email admin@demo.test --admin-password change-me
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context, schema_exists

from apps.core.logging import ctx, get_logger

log = get_logger("provisioning")


class Command(BaseCommand):
    help = "Provision a new school tenant (schema + domain + admin user)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--schema", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--domain", required=True)
        parser.add_argument("--admin-email", required=True)
        parser.add_argument("--admin-password", required=True)

    def handle(self, *args, **opts) -> None:
        from apps.tenants.models import Client, Domain

        schema = opts["schema"]
        if schema_exists(schema):
            raise CommandError(f"Schema '{schema}' already exists.")

        client = Client(schema_name=schema, name=opts["name"])
        client.save()  # auto-creates + migrates the schema
        Domain.objects.create(domain=opts["domain"], tenant=client, is_primary=True)

        # Create the school admin *inside* the tenant schema.
        from apps.accounts.models import Role, User

        with schema_context(schema):
            User.objects.create_superuser(
                username=opts["admin_email"],
                email=opts["admin_email"],
                password=opts["admin_password"],
                role=Role.ADMIN,
            )

        log.info(
            "tenant provisioned schema=%s domain=%s",
            schema,
            opts["domain"],
            **ctx(entity=schema, action="provision_tenant"),
        )
        self.stdout.write(self.style.SUCCESS(f"Provisioned '{opts['name']}' at {opts['domain']}"))
