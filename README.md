# SFMS — School Fee Management System

Multi-tenant school fee management. Each school is an isolated PostgreSQL schema
(django-tenants). See [`CLAUDE.md`](./CLAUDE.md) for the full architecture and
coding contract.

## Stack

| Layer       | Tech |
|-------------|------|
| Frontend    | React + TypeScript + Tailwind (Vite) |
| Backend     | Django + DRF + django-tenants |
| Database    | PostgreSQL (tsvector/GIN search) |
| Cache       | Redis |
| Queue       | Celery + RabbitMQ |
| Storage     | MinIO (S3-compatible) |
| Monitoring  | Sentry |

## Quickstart

```bash
cp .env.example .env

# Bring up infra + backend.
docker compose up -d postgres redis rabbitmq minio
docker compose build backend
docker compose up -d backend        # entrypoint migrates public + tenant schemas

# One-time platform + demo school setup.
docker compose run --rm backend python manage.py bootstrap_public --domain localhost
docker compose run --rm backend python manage.py provision_tenant \
    --schema demo --name "Demo School" --domain demo.localhost \
    --admin-email admin@demo.test --admin-password change-me-please

# Frontend.
docker compose up -d frontend       # http://localhost:5173
```

### Endpoints

- Public health: `http://localhost:8000/health/`
- Public/platform admin: `http://localhost:8000/admin/`
- Tenant API (send `Host: demo.localhost`): `http://localhost:8000/api/v1/…`
- MinIO console: `http://localhost:9001`
- RabbitMQ management: `http://localhost:15672`

> Tenants resolve from the **request host** (subdomain). Point `demo.localhost`
> (and friends) at `127.0.0.1`, or pass a `Host` header. The frontend never sends
> a tenant id — the schema is chosen server-side.

### Auth flow (dev)

Each school signs in from its own subdomain. Browsers resolve `*.localhost` to
`127.0.0.1` automatically, so no `/etc/hosts` edits are needed.

1. **Sign up** at `http://localhost:5173/signup` — creates the school and returns
   a **school code** (e.g. `GHS-3000`) + your sign-in URL.
2. **Sign in** at `http://<slug>.localhost:5173/login` (e.g.
   `http://greenfield-high.localhost:5173/login`). On the apex host the login page
   resolves the school code to the subdomain first.
3. The app then runs on that subdomain and every API call is scoped to the school.

## Tests & lint

```bash
docker compose run --rm backend pytest
docker compose run --rm backend ruff check .
docker compose run --rm backend black --check .

cd frontend && npm install && npm run typecheck && npm run lint
```

## Layout

```
backend/   Django project (config/) + apps/ (core, tenants, accounts, schools,
           students, fees, collections, staff, expenses, inventory, finance)
frontend/  Vite + React + Tailwind; feature-first under src/features
```
