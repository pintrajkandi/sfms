#!/usr/bin/env bash
set -euo pipefail

# Wait for Postgres before doing anything schema-related.
echo "[info] waiting for postgres at ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}"
until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
    s.connect((os.getenv('POSTGRES_HOST','postgres'), int(os.getenv('POSTGRES_PORT','5432'))))" 2>/dev/null; do
    sleep 1
done

# Only the web/worker entrypoint runs migrations; keep it idempotent.
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "[info] migrating public (shared) schema"
    python manage.py migrate_schemas --shared --noinput
    echo "[info] migrating tenant schemas"
    python manage.py migrate_schemas --tenant --noinput || true
    # Always ensure the public tenant + localhost domain exist so the platform
    # (admin/health/onboarding) is reachable — idempotent.
    echo "[info] ensuring public tenant + domain"
    python manage.py bootstrap_public --domain "${PUBLIC_DOMAIN:-localhost}" || true
fi

exec "$@"
