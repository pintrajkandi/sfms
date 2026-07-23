"""Shared CSV → UdiseSchool import logic (used by the admin upload + command)."""

from __future__ import annotations

import csv
from typing import TextIO

from .models import UdiseSchool

# UDISE CSV column -> model field. Only these columns are imported.
FIELD_MAP = {
    "stateId": "state_id",
    "stateName": "state_name",
    "districtName": "district_name",
    "address": "address",
    "classTo": "class_to",
    "email": "email",
    "schoolName": "school_name",
}


def clean_email(raw: str) -> str:
    """UDISE obfuscates emails as name[at]gmail[dot]com — restore them."""
    if not raw:
        return ""
    return raw.strip().replace("[at]", "@").replace("[dot]", ".").replace(" ", "")


def import_rows(fp: TextIO, batch_size: int = 2000) -> dict:
    """Import an open UDISE CSV text stream efficiently in memory-friendly batches."""
    reader = csv.DictReader(fp)

    rows = skipped = created = 0
    batch: list[UdiseSchool] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for row in reader:
        rows += 1
        data = {field: (row.get(col) or "").strip() for col, field in FIELD_MAP.items()}
        data["email"] = clean_email(data["email"])

        if not data["school_name"]:
            skipped += 1
            continue

        # Prevent sending duplicate keys within the exact same batch to the DB
        key = (data["school_name"], data["address"], data["state_id"])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        batch.append(UdiseSchool(**data))

        # Process when chunk reaches batch limit
        if len(batch) >= batch_size:
            created += _process_batch(batch)
            batch = []
            seen_keys.clear()

    # Process remaining rows
    if batch:
        created += _process_batch(batch)

    return {"rows": rows, "created": created, "skipped": skipped}


def _process_batch(batch: list[UdiseSchool]) -> int:
    """Batch upsert to DB. Performs insert or update at DB-level without PK issues."""
    try:
        # Native DB-level ON CONFLICT DO UPDATE (PostgreSQL, MySQL 8+, SQLite 3.24+)
        results = UdiseSchool.objects.bulk_create(
            batch,
            batch_size=len(batch),
            update_conflicts=True,
            unique_fields=["school_name", "address", "state_id"],
            update_fields=["state_name", "district_name", "class_to", "email"],
        )
        return len(results) if results else len(batch)

    except Exception:
        # Fallback for databases that don't support native composite field upserts
        names = {s.school_name for s in batch}
        addresses = {s.address for s in batch}

        # Query existing records from DB WITH primary keys set
        existing_schools = {
            (s.school_name, s.address, s.state_id): s
            for s in UdiseSchool.objects.filter(
                school_name__in=names, address__in=addresses
            )
        }

        to_create = []
        to_update = []

        for school in batch:
            key = (school.school_name, school.address, school.state_id)
            if key in existing_schools:
                # Retrieve instance fetched from DB so primary key (pk) is attached
                existing_obj = existing_schools[key]
                existing_obj.state_name = school.state_name
                existing_obj.district_name = school.district_name
                existing_obj.class_to = school.class_to
                existing_obj.email = school.email
                to_update.append(existing_obj)
            else:
                to_create.append(school)

        if to_create:
            UdiseSchool.objects.bulk_create(to_create, batch_size=len(to_create))

        if to_update:
            UdiseSchool.objects.bulk_update(
                to_update,
                fields=["state_name", "district_name", "class_to", "email"],
                batch_size=len(to_update),
            )

        return len(to_create)