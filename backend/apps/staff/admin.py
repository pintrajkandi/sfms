"""No admin here — this app's models are tenant-scoped (TENANT_APPS); their tables
do not exist in the public schema, so registering them on the admin would 500.
The platform console lives in apps.tenants.admin; schools use the app UI (CLAUDE.md §3)."""
