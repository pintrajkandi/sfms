"""
Verified database backups + restore drill (CLAUDE.md §10).

`create_backup` runs `pg_dump -Fc` over the whole cluster, checksums the file,
and records an exact per-table row-count manifest. `verify_backup` re-hashes the
dump (integrity) and — the real drill — restores it into a throwaway scratch
database and compares the restored row counts against the manifest, then drops
the scratch DB. Backups are verified, not assumed.

pg_dump / pg_restore / createdb must be on PATH (postgresql-client). When they
are absent the functions degrade gracefully: create_backup raises, verify does an
integrity-only check.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import uuid
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.utils import timezone

from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

from .models import BackupRun

log = get_logger("tenants.backups")

BACKUP_DIR = os.environ.get("BACKUP_DIR", "/tmp/sfms-backups")
_SYSTEM_SCHEMAS = ["pg_catalog", "information_schema", "pg_toast"]


def _db() -> dict:
    d = settings.DATABASES["default"]
    return {
        "host": d.get("HOST", "postgres"),
        "port": str(d.get("PORT", 5432)),
        "user": d.get("USER", "sfms"),
        "password": d.get("PASSWORD", "sfms"),
        "name": d.get("NAME", "sfms"),
    }


def _pg_env() -> dict:
    env = os.environ.copy()
    env["PGPASSWORD"] = _db()["password"]
    return env


def tools_available() -> bool:
    return all(shutil.which(t) for t in ("pg_dump", "pg_restore", "createdb", "dropdb"))


def table_counts(cursor=None) -> dict[str, int]:
    """Exact row count per base table across all non-system schemas."""
    own = cursor is None
    cursor = cursor or connection.cursor()
    try:
        cursor.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema <> ALL(%s)
            ORDER BY table_schema, table_name
            """,
            [_SYSTEM_SCHEMAS],
        )
        tables = cursor.fetchall()
        counts: dict[str, int] = {}
        for schema, name in tables:
            cursor.execute(f'SELECT count(*) FROM "{schema}"."{name}"')
            counts[f"{schema}.{name}"] = cursor.fetchone()[0]
        return counts
    finally:
        if own:
            cursor.close()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_counts(expected: dict, actual: dict) -> list[dict]:
    """Return per-table mismatches between two count manifests."""
    mismatches = []
    for table, exp in expected.items():
        act = actual.get(table)
        if act != exp:
            mismatches.append({"table": table, "expected": exp, "actual": act})
    for table in actual:
        if table not in expected:
            mismatches.append({"table": table, "expected": None, "actual": actual[table]})
    return mismatches


def create_backup(*, label: str = "", actor=None) -> BackupRun:
    """Dump the database, checksum it, and snapshot a row-count manifest."""
    if not shutil.which("pg_dump"):
        raise ServiceError("pg_dump not available (install postgresql-client).")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    label = label or datetime.now().strftime("auto-%Y%m%d-%H%M%S")
    path = os.path.join(BACKUP_DIR, f"{label}-{uuid.uuid4().hex[:8]}.dump")
    db = _db()

    counts = table_counts()
    try:
        subprocess.run(
            [
                "pg_dump",
                "-Fc",
                "-h",
                db["host"],
                "-p",
                db["port"],
                "-U",
                db["user"],
                "-d",
                db["name"],
                "-f",
                path,
            ],
            env=_pg_env(),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ServiceError(f"pg_dump failed: {exc.stderr.decode()[:200]}") from exc

    run = BackupRun.objects.create(
        label=label,
        path=path,
        sha256=_sha256(path),
        size_bytes=os.path.getsize(path),
        table_count_total=sum(counts.values()),
        table_counts=counts,
    )
    log.info(
        "backup created label=%s size=%s tables=%s",
        label,
        run.size_bytes,
        len(counts),
        **ctx(user=getattr(actor, "id", "-"), entity=run.id, action="create_backup"),
    )
    return run


def verify_backup(run: BackupRun, *, actor=None) -> BackupRun:
    """Re-hash the dump and restore-drill it into a scratch DB; record the result."""
    report: dict = {"integrity_ok": False, "restore_ok": None, "mismatches": []}

    if not run.path or not os.path.exists(run.path):
        run.status = BackupRun.Status.FAILED
        run.error = "backup file missing"
        run.save(update_fields=["status", "error"])
        return run

    report["integrity_ok"] = _sha256(run.path) == run.sha256

    if tools_available() and report["integrity_ok"]:
        db = _db()
        scratch = f"sfms_drill_{uuid.uuid4().hex[:8]}"
        try:
            subprocess.run(
                ["createdb", "-h", db["host"], "-p", db["port"], "-U", db["user"], scratch],
                env=_pg_env(),
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "pg_restore",
                    "-h",
                    db["host"],
                    "-p",
                    db["port"],
                    "-U",
                    db["user"],
                    "-d",
                    scratch,
                    "--no-owner",
                    run.path,
                ],
                env=_pg_env(),
                check=False,
                capture_output=True,  # pg_restore warns are non-fatal
            )
            restored = _counts_via_psql(scratch)
            mismatches = compare_counts(run.table_counts, restored)
            report["restore_ok"] = len(mismatches) == 0
            report["mismatches"] = mismatches[:50]
        except subprocess.CalledProcessError as exc:
            report["restore_ok"] = False
            report["error"] = exc.stderr.decode()[:200]
        finally:
            subprocess.run(
                [
                    "dropdb",
                    "-h",
                    db["host"],
                    "-p",
                    db["port"],
                    "-U",
                    db["user"],
                    "--if-exists",
                    scratch,
                ],
                env=_pg_env(),
                check=False,
                capture_output=True,
            )

    ok = report["integrity_ok"] and (report["restore_ok"] in (True, None))
    run.verified = ok and report["integrity_ok"]
    run.verified_at = timezone.now()
    run.status = BackupRun.Status.VERIFIED if ok else BackupRun.Status.FAILED
    run.report = report
    run.save(update_fields=["verified", "verified_at", "status", "report"])

    level = log.info if ok else log.error
    level(
        "backup verified label=%s integrity=%s restore=%s",
        run.label,
        report["integrity_ok"],
        report["restore_ok"],
        **ctx(user=getattr(actor, "id", "-"), entity=run.id, action="verify_backup"),
    )
    return run


# --------------------------------------------------------------------------- #
# Per-school (per-schema) backups — durable in object storage, restorable from
# the platform admin. One dump per tenant schema so a single school can be
# handed over or rolled back independently.
# --------------------------------------------------------------------------- #
def schema_table_counts(schema_name: str, cursor=None) -> dict[str, int]:
    """Exact row count per base table for a single schema."""
    own = cursor is None
    cursor = cursor or connection.cursor()
    try:
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_type = 'BASE TABLE' AND table_schema = %s
            ORDER BY table_name
            """,
            [schema_name],
        )
        counts: dict[str, int] = {}
        for (name,) in cursor.fetchall():
            cursor.execute(f'SELECT count(*) FROM "{schema_name}"."{name}"')
            counts[f"{schema_name}.{name}"] = cursor.fetchone()[0]
        return counts
    finally:
        if own:
            cursor.close()


def create_schema_backup(*, client, label: str = "", actor=None) -> BackupRun:
    """pg_dump one school's schema, checksum it, and store it in object storage."""
    if not shutil.which("pg_dump"):
        raise ServiceError("pg_dump not available (install postgresql-client).")

    schema = client.schema_name
    os.makedirs(BACKUP_DIR, exist_ok=True)
    label = label or f"{schema}-{datetime.now():%Y%m%d-%H%M%S}"
    local = os.path.join(BACKUP_DIR, f"{label}-{uuid.uuid4().hex[:8]}.dump")
    db = _db()

    counts = schema_table_counts(schema)
    try:
        subprocess.run(
            [
                "pg_dump",
                "-Fc",
                "--schema",
                schema,
                "-h",
                db["host"],
                "-p",
                db["port"],
                "-U",
                db["user"],
                "-d",
                db["name"],
                "-f",
                local,
            ],
            env=_pg_env(),
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ServiceError(f"pg_dump failed: {exc.stderr.decode()[:200]}") from exc

    sha, size = _sha256(local), os.path.getsize(local)
    key = f"backups/{schema}/{os.path.basename(local)}"
    from django.core.files import File
    from django.core.files.storage import default_storage

    with open(local, "rb") as f:
        default_storage.save(key, File(f))
    try:
        os.remove(local)  # object storage is the durable copy
    except OSError:
        pass

    run = BackupRun.objects.create(
        client=client,
        schema_name=schema,
        label=label,
        storage_key=key,
        sha256=sha,
        size_bytes=size,
        table_count_total=sum(counts.values()),
        table_counts=counts,
    )
    log.info(
        "school backup created schema=%s size=%s tables=%s",
        schema,
        size,
        len(counts),
        **ctx(user=getattr(actor, "id", "-"), entity=run.id, action="create_schema_backup"),
    )
    return run


def materialize(run: BackupRun) -> str:
    """Return a local path to the dump, downloading from storage if needed."""
    if run.path and os.path.exists(run.path):
        return run.path
    if run.storage_key:
        from django.core.files.storage import default_storage

        os.makedirs(BACKUP_DIR, exist_ok=True)
        local = os.path.join(BACKUP_DIR, os.path.basename(run.storage_key))
        with default_storage.open(run.storage_key, "rb") as src, open(local, "wb") as dst:
            shutil.copyfileobj(src, dst)
        return local
    raise ServiceError("Backup file is not available (no local path or storage key).")


def restore_schema_backup(run: BackupRun, *, actor=None) -> BackupRun:
    """DESTRUCTIVE: drop the school's schema and restore it from this backup."""
    if not run.schema_name:
        raise ServiceError("This is not a per-school backup; cannot restore a schema.")
    if not tools_available():
        raise ServiceError("pg_restore not available (install postgresql-client).")

    local = materialize(run)
    if _sha256(local) != run.sha256:
        raise ServiceError("Backup checksum mismatch — refusing to restore a corrupt dump.")

    db = _db()
    schema = run.schema_name

    import psycopg

    conn = psycopg.connect(
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        dbname=db["name"],
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            cur.execute(f'CREATE SCHEMA "{schema}"')
    finally:
        conn.close()

    # -Fc --schema dumps schema-qualified objects; restore recreates them.
    proc = subprocess.run(
        [
            "pg_restore",
            "-h",
            db["host"],
            "-p",
            db["port"],
            "-U",
            db["user"],
            "-d",
            db["name"],
            "--no-owner",
            local,
        ],
        env=_pg_env(),
        check=False,
        capture_output=True,
    )
    restored = schema_table_counts(schema)
    mismatches = compare_counts(run.table_counts, restored)
    ok = len(mismatches) == 0
    level = log.info if ok else log.error
    level(
        "school backup restored schema=%s ok=%s mismatches=%s",
        schema,
        ok,
        len(mismatches),
        **ctx(user=getattr(actor, "id", "-"), entity=run.id, action="restore_schema_backup"),
    )
    if not ok and proc.stderr:
        log.warning(
            "pg_restore stderr: %s",
            proc.stderr.decode()[:300],
            **ctx(action="restore_schema_backup"),
        )
    return run


def _counts_via_psql(dbname: str) -> dict[str, int]:
    """Row counts in a freshly-restored scratch DB (separate connection)."""
    import psycopg

    db = _db()
    conn = psycopg.connect(
        host=db["host"],
        port=db["port"],
        user=db["user"],
        password=db["password"],
        dbname=dbname,
    )
    try:
        with conn.cursor() as cur:
            return table_counts(cur)
    finally:
        conn.close()
