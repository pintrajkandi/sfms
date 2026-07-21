"""Create a verified database backup + run the restore drill."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.tenants.backups import create_backup, verify_backup


class Command(BaseCommand):
    help = "Dump the database, checksum it, and verify via a restore drill."

    def add_arguments(self, parser):
        parser.add_argument("--label", default="", help="Human label for this backup")
        parser.add_argument("--no-verify", action="store_true", help="Skip the restore drill")

    def handle(self, *args, **opts):
        run = create_backup(label=opts["label"])
        self.stdout.write(
            f"backup created: {run.label} ({run.size_bytes} bytes, "
            f"{len(run.table_counts)} tables, sha256={run.sha256[:12]}…)"
        )
        if not opts["no_verify"]:
            run = verify_backup(run)
            self.stdout.write(f"verify: status={run.status} verified={run.verified}")
            self.stdout.write(json.dumps(run.report, indent=2, default=str))
