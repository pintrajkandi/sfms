"""Verified backups — manifest counts, comparison, integrity (CLAUDE.md §8, §10).

The real restore drill needs pg_dump/pg_restore (exercised live, not in pytest);
here we cover the pure manifest/comparison logic and the integrity/guard paths.
"""

import pytest

from apps.tenants import backups
from apps.tenants.models import BackupRun

pytestmark = [pytest.mark.django_db]


def test_compare_counts_flags_mismatches_and_extras():
    expected = {"public.a": 5, "public.b": 3}
    actual = {"public.a": 5, "public.b": 2, "public.c": 1}
    mismatches = backups.compare_counts(expected, actual)
    tables = {m["table"] for m in mismatches}
    assert "public.b" in tables  # count differs
    assert "public.c" in tables  # unexpected extra
    assert "public.a" not in tables  # matches


def test_compare_counts_clean_when_equal():
    counts = {"public.a": 1, "public.b": 2}
    assert backups.compare_counts(counts, dict(counts)) == []


def test_table_counts_returns_row_counts(db):
    counts = backups.table_counts()
    assert isinstance(counts, dict)
    # the shared tenant registry table is always present in the public schema
    assert any(t.endswith(".tenants_client") for t in counts)


def test_create_backup_guarded_without_pg_dump(db, monkeypatch):
    from apps.core.services import ServiceError

    monkeypatch.setattr(backups.shutil, "which", lambda _: None)
    with pytest.raises(ServiceError):
        backups.create_backup(label="unit")


def test_verify_missing_file_marks_failed(db):
    run = BackupRun.objects.create(label="ghost", path="/nonexistent/x.dump", sha256="abc")
    run = backups.verify_backup(run)
    assert run.status == BackupRun.Status.FAILED
    assert run.error == "backup file missing"
