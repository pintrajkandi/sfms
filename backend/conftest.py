"""
Pytest fixtures — every tenant-aware test runs INSIDE a tenant schema so we never
accidentally touch `public` (CLAUDE.md §8).
"""

import pytest
from django.db import connection


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Create a throwaway tenant schema for the test session."""
    with django_db_blocker.unblock():
        from apps.tenants.models import Client, Domain

        tenant, created = Client.objects.get_or_create(
            schema_name="test", defaults={"name": "Test School"}
        )
        if created:
            Domain.objects.create(domain="test.localhost", tenant=tenant, is_primary=True)
    yield


@pytest.fixture
def tenant_ctx(db):
    """Activate the test tenant schema for the duration of a test."""
    from django_tenants.utils import schema_context

    with schema_context("test"):
        yield
    connection.set_schema_to_public()
