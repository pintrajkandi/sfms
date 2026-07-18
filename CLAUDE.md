# CLAUDE.md — School Fee Management System (SFMS)

Guidance for Claude Code (and humans) working in this repository.

> **Status:** Greenfield. This file is the architectural blueprint + the coding
> contract. Directory layout described below is the **target**; create paths as
> you build them and keep this file in sync when structure changes.

---

## 1. What we are building

A multi-tenant **School Fee Management System**. Each school is an isolated
tenant. Core domains (derived from the UI mockups in `image/`):

| Module          | Responsibility |
|-----------------|----------------|
| **Dashboard**   | Fee collection KPIs, monthly collection charts, category breakdown, recent payments, upcoming due dates, quick actions. |
| **Students**    | Enrollment (personal, contact, guardian, photo), student list, student detail with fee breakdown + payment history + payment progress. |
| **Fee Structures** | Fee types (Tuition, Lab, Library, Transport, Sports, Exam, Activities), fee categories, per-class/academic-year fee plans. |
| **Fee Collection** | 3-step wizard: Student Info → Fee Details → Payment. Search-driven. |
| **Invoices**    | Invoice generation, discounts, late fees, print / PDF download. |
| **Payments**    | Record payment, payment history, statuses: `paid`, `pending`, `overdue`, `partial`. |
| **Staff / Teachers** | Add teacher, **Teacher Payout** with approval workflow: `Form Submitted → HOD Review → Finance Review → Payment Processed`. Base + bonus/incentive − deductions = net. |
| **Expenses**    | Submit expense (title, category, amount, currency, reimbursable flag, vendor, project/cost center, notes). |
| **Inventory**   | School assets (category, SKU, unit of measure, condition, purchase info, supplier, warranty, photo, active status). |
| **Finance / Accounts** | Income vs expense, expense breakdown, net savings trend, transactions ledger. |
| **Reports / Analytics** | Aggregations + exports (CSV/PDF/XLSX), generated async. |
| **School Settings** | Per-tenant: School Info, Branding & Logos, Invoice Settings, Contact Details, Academic Year, Notifications. |

Money is domain-critical: **always store amounts as `Decimal` (never float)** and
persist the currency. Never do financial math in JS with `number`; use minor
units or a decimal lib on the frontend.

---

## 2. Tech stack

- **Frontend:** React + TypeScript + Tailwind CSS
- **Backend:** Django + Django REST Framework, **django-tenants** (schema-based multi-tenancy)
- **Database:** PostgreSQL — full-text search via `tsvector` + **GIN** indexes
- **Cache:** Redis (cache, sessions, rate limiting, Celery result backend)
- **Queue:** Celery workers with **RabbitMQ** broker
- **Object storage:** MinIO (S3-compatible, self-hosted) — student/item photos, logos, generated PDFs/exports
- **Backup / HA:** pgBackRest → offsite storage + a warm standby (streaming replication)
- **Monitoring:** Sentry (backend + frontend)

---

## 3. Multi-tenancy — READ BEFORE TOUCHING DATA

We use **django-tenants** (PostgreSQL schema per tenant).

- **Public (shared) schema** holds: tenant registry (`Client`/`Tenant` + `Domain`),
  and anything genuinely global. Put these apps in `SHARED_APPS`.
- **Tenant schema** holds all business data: students, fees, payments, invoices,
  staff, expenses, inventory, school settings. Put these in `TENANT_APPS`.
- A tenant is resolved from the request host (subdomain) by
  `TenantMainMiddleware`. **Never** hardcode or cross a tenant boundary.

**Hard rules:**
1. Never write a query that reaches across schemas for business data.
2. Never trust a tenant id from the request body — the tenant comes from the
   routed schema only.
3. Management commands that touch tenant data must run per-schema
   (`tenant_command` / iterate schemas), never blindly against `public`.
4. New business models → the app must be in `TENANT_APPS`. If you're unsure
   whether a model is shared or tenant-scoped, it's **tenant-scoped**.

### Authentication & onboarding

Each school signs in from **its own subdomain** (`<slug>.feeledger.app`; dev uses
`<slug>.localhost`). `Client.slug` is that subdomain; `Client.code` is the human
**school code** (e.g. `GHS-3000`) shown on the sign-in screen.

- **Onboarding is public** (shared schema): `POST /api/v1/onboarding/signup/`
  provisions the tenant (schema + domain + first admin) via
  `apps.tenants.services.provision_school`. `…/resolve/` maps a school code →
  subdomain so the sign-in page can route to the right tenant.
- **Login is tenant-scoped** (`POST /api/v1/auth/{csrf,login,logout,me}/`): served
  on the subdomain, so the tenant — and its user table — is already resolved by
  `TenantMainMiddleware`. Sessions are cache-backed with tenant-scoped keys, so a
  session **cannot** cross schemas. Users live in `TENANT_APPS` (per-school).
- The frontend never sends a tenant id; the API host mirrors the page host
  (`apiBase()` in `frontend/src/api/client.ts`).
- **Django admin is public-only.** `/admin/` is mounted solely in
  `config/urls_public.py` (public schema, master/platform admins). The tenant
  URLconf (`config/urls.py`) does **not** mount admin, so school staff can never
  reach it — they use the app UI + tenant auth API. Static assets are served by
  WhiteNoise (first in `MIDDLEWARE`), so admin CSS/JS load under gunicorn.

### First-run onboarding sequence

New self-service schools follow **register → verify email → complete settings → use app**:

1. **Sign-up** creates the first admin as `email_verified=False` and emails a signed
   verification link (`apps.accounts.tokens`, 3-day expiry). Manually-provisioned
   admins (`provision_tenant`) and the public superuser default to verified.
2. **Login is blocked** for unverified users (`403`, `code: "email_unverified"`);
   the UI offers a resend. `/auth/verify-email/` flips the flag.
3. **Settings hard-gate:** `/auth/me/` returns `settings_complete` (true once
   `SchoolSettings` has a name). The frontend `OnboardingGate` redirects every
   route to `/settings` until the profile is saved, then unlocks the app.

Optional **Auth0 SSO** (`/auth/auth0/`) is env-gated (`AUTH0_DOMAIN`+`AUTH0_AUDIENCE`);
when unset it returns `503` and password login is used.

---

## 4. Repository layout (target)

```
sfms/
├── CLAUDE.md
├── docker-compose.yml            # postgres, redis, rabbitmq, minio, backend, worker, beat, frontend
├── .env.example
├── backend/
│   ├── manage.py
│   ├── pyproject.toml            # ruff + black + mypy config
│   ├── config/                   # project package
│   │   ├── settings/             # base.py, dev.py, prod.py
│   │   ├── celery.py
│   │   ├── logging.py            # info/warn/error config (see §9)
│   │   └── urls.py
│   └── apps/
│       ├── core/                 # base models, mixins, pagination, search, logging helpers
│       ├── tenants/              # SHARED: Client/Domain models, provisioning
│       ├── accounts/             # users, roles/permissions, auth
│       ├── schools/              # school settings, branding, academic year
│       ├── students/
│       ├── staff/                # teachers + payouts (approval workflow)
│       ├── fees/                 # fee types, categories, structures/plans
│       ├── collections/          # fee collection, payments, invoices
│       ├── expenses/
│       ├── inventory/
│       ├── finance/              # ledger + accounts dashboard aggregation
│       ├── reports/              # async report generation/exports
│       └── notifications/        # reminders, email/SMS dispatch (Celery)
└── frontend/
    ├── package.json
    ├── tailwind.config.ts
    └── src/
        ├── api/                  # typed API client, generated types
        ├── components/           # shared UI
        ├── features/             # one folder per module above
        ├── hooks/
        ├── lib/                  # money, dates, formatting
        └── routes/
```

Note: `ecr.sh`, `ecs.sh`, `s3.sh` and `image/` are standalone (AWS admin scripts
+ UI reference mockups). They are **not** part of the application build.

---

## 5. Backend conventions

- **Layering:** `models → services → serializers → views/viewsets → urls`.
  Business logic (money math, workflow transitions, invoice/late-fee calculation)
  lives in **service functions**, not in views or serializers. Views stay thin.
- **DRF:** ViewSets + routers. Explicit serializers per read/write shape. Always
  paginate list endpoints. Validate in serializers; enforce invariants in services.
- **Base model:** every tenant model extends a `TimeStampedModel`
  (`created_at`, `updated_at`) from `apps.core`. Soft-delete via `is_active`/
  `deleted_at` where the UI implies archival (e.g. inventory `Active in Inventory`).
- **Money:** `DecimalField(max_digits=12, decimal_places=2)` + a currency field.
- **State machines:** payout approval and payment/invoice statuses use explicit
  status enums (`TextChoices`) with guarded transition functions in services —
  no free-form status writes from the view.
- **Migrations:** one logical change per migration; never edit an applied migration.
- **Idempotency:** payment recording and payout processing must be idempotent
  (guard against double submit) — use a unique constraint or idempotency key.

### Search (tsvector / GIN)
- Add a `SearchVectorField` + `GinIndex` to searchable models (students by name/
  id/guardian, invoices, inventory). Keep the vector updated via a trigger or
  `SearchVector` on save. Query with `SearchQuery`/`SearchRank`. Do **not**
  implement search with chained `icontains` on large tables.

### Async (Celery + RabbitMQ)
- Anything slow or external is a task: PDF/invoice generation, report exports,
  email/SMS reminders, bulk imports. Keep tasks **idempotent** and small; pass
  ids, not objects. Tasks must set the correct tenant schema before touching data.
- Schedule recurring work (overdue-fee detection, due-date reminders) via Celery beat.

### Storage (MinIO)
- All uploads/generated files go to MinIO via `django-storages` (S3 backend).
  Never write user files to the local filesystem or serve them from the app.
  Use presigned URLs for downloads. Buckets are namespaced per tenant.

### Caching (Redis)
- Cache dashboard aggregates and expensive report queries with explicit TTLs and
  **tenant-scoped cache keys** (prefix every key with the schema/tenant). Invalidate
  on the relevant write. Never let one tenant read another's cached data.

---

## 6. Frontend conventions

- React + TypeScript, **strict mode on**. No `any` in committed code.
- Tailwind for styling; extract shared primitives into `components/`. Match the
  visual language in `image/` (card-based, indigo/violet accent).
- Feature-first structure under `src/features/<module>`.
- Server state via a typed API client in `src/api`; keep API response types in
  sync with DRF serializers.
- **Money & dates:** format through `src/lib` helpers only. Never render raw
  floats for currency.
- Forms (multi-step fee collection, payout, add-student/inventory) use a schema
  validator (e.g. Zod) and show inline validation like the mockups.

---

## 7. Environment & local dev

- `docker-compose up` brings up postgres, redis, rabbitmq, minio, backend, celery
  worker, celery beat, and frontend.
- Copy `.env.example` → `.env`; never commit real secrets. All config comes from
  env vars (12-factor). No secrets in `settings/`.
- First run: migrate `public`, bootstrap the public tenant, then provision a school.

Common commands (run inside the `backend` container, e.g. `docker compose run --rm backend …`):
```bash
# backend
python manage.py migrate_schemas --shared          # public schema
python manage.py migrate_schemas --tenant          # all tenant schemas
python manage.py bootstrap_public --domain localhost   # public tenant + domain (idempotent)
python manage.py provision_tenant \                # provision a school
    --schema demo --name "Demo School" --domain demo.localhost \
    --admin-email admin@demo.test --admin-password <pw>
pytest                                             # tests
ruff check . && black --check . && mypy .          # lint + types

# frontend
npm run dev
npm run build
npm run lint && npm run typecheck
```

> Note: our provisioning command is `provision_tenant` (not django-tenants'
> built-in `create_tenant`, which it deliberately does not shadow).

---

## 8. Testing

- Backend: pytest + `pytest-django`. Every service function with money math or a
  workflow transition needs unit tests. Tenant-aware tests must run inside a tenant
  schema. Cover: fee calculation, discounts, late fees, partial payments, payout
  approval transitions, and tenant isolation (a tenant cannot read another's data).
- Frontend: component + form-validation tests for the wizards.
- Don't mark work done until the relevant tests and linters pass — report real output.

---

## 9. Logging — levels are exactly `info`, `warn`, `error`

**Standard: three levels only. Configure Python logging so nothing below `info`
is emitted in normal operation, and normalize the names to `info` / `warn` /
`error` in the formatter.** (Python's native level is `WARNING`; render it as
`warn` in our log format so output reads `[info] [warn] [error]`.)

Use them consistently — same meaning on backend and frontend:

- **`info`** — normal, expected events worth recording: payment recorded, invoice
  generated, payout advanced a stage, tenant provisioned, report export finished,
  reminder batch sent. Business audit trail.
- **`warn`** — recoverable / degraded / suspicious but handled: retryable task
  retrying, cache miss fallback, deprecated endpoint hit, validation rejected a
  request, overdue fee auto-flagged, near-quota storage. Something a human may
  want to review; the system kept working.
- **`error`** — a failure that broke an operation: unhandled exception, failed
  payment write, MinIO/DB/RabbitMQ unreachable, payout transition violated an
  invariant, task exhausted retries. Always attach context (tenant, entity id).

Rules:
- **Never log** secrets, full card/payment credentials, passwords, or full PII.
  Log ids and amounts, not raw personal data.
- Every log line carries structured context: `tenant`, `user`, `entity`, `action`.
- Do not use `debug`/`critical`/`trace` as app-facing levels — collapse into the
  three above. (Fatal startup failures may use `error`.)
- Backend routes through `config/logging.py`; frontend uses a small logger wrapper
  exposing `log.info/warn/error` — no bare `console.log` in committed code.
- Sentry captures `error` (and optionally `warn`) — see §10.

---

## 10. Monitoring, backup, HA

- **Sentry:** initialized on backend (Django + Celery integrations) and frontend.
  Report `error`-level events; scrub PII/secrets before send. Tag events with the
  tenant. DSNs come from env vars.
- **pgBackRest:** full + incremental backups to offsite storage; a warm **standby**
  via streaming replication. Backups and restores are verified, not assumed —
  document the restore drill when the config lands.

---

## 11. Working agreements for Claude

- Respect the tenant boundary in every query, task, cache key, and file path (§3).
- Money is `Decimal` end-to-end; currency is always persisted (§1).
- Business logic in services; views/serializers stay thin (§5).
- Logging uses only `info` / `warn` / `error`, structured, no secrets/PII (§9).
- Keep this file updated when architecture or structure changes.
- When something is done, verify it (tests/linters) and report real results.
