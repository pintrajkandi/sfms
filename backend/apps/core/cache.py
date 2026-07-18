"""Tenant-scoped cache key function — one tenant can NEVER read another's cache."""

from django_tenants.utils import get_public_schema_name


def current_schema() -> str:
    """Return the active tenant schema name, or the public schema outside a request."""
    from django.db import connection

    schema = getattr(connection, "schema_name", None)
    return schema or get_public_schema_name()


def tenant_key_func(key: str, key_prefix: str, version: int) -> str:
    """Django CACHES KEY_FUNCTION — prefixes every key with the tenant schema."""
    return f"{current_schema()}:{key_prefix}:{version}:{key}"
