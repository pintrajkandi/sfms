"""Import UDISE school CSV(s) from the shell.

python manage.py import_udise_schools /path/schools_*.csv
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django_tenants.utils import schema_context

from apps.udise.importer import import_rows


class Command(BaseCommand):
    help = "Import UDISE school CSV file(s) into the public UdiseSchool table."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", nargs="+", help="One or more CSV file paths")

    def handle(self, *args, **opts):
        total_new = total_rows = 0
        # UdiseSchool is a shared (public-schema) model.
        with schema_context("public"):
            for path in opts["csv_path"]:
                p = Path(path)
                if not p.exists():
                    raise CommandError(f"File not found: {p}")
                with p.open(newline="", encoding="utf-8", errors="replace") as f:
                    result = import_rows(f)
                total_new += result["created"]
                total_rows += result["rows"]
                self.stdout.write(
                    self.style.SUCCESS(f"{p.name}: {result['created']} new / {result['rows']} rows")
                )
        self.stdout.write(self.style.SUCCESS(f"Done — {total_new} new from {total_rows} rows."))
