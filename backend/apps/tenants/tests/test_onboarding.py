"""School onboarding: slug/code generation + uniqueness (CLAUDE.md §8)."""

import pytest

from apps.tenants.services import _generate_code, _unique_slug, normalize_slug, slug_available

pytestmark = [pytest.mark.django_db]


def test_normalize_slug():
    assert normalize_slug("Greenfield High School!") == "greenfield-high-school"


def test_reserved_and_short_slugs_unavailable():
    assert slug_available("app") is False
    assert slug_available("a") is False
    assert slug_available("greenfield-high") is True


def test_generated_code_shape():
    code = _generate_code("Greenfield High Public School")
    prefix, _, suffix = code.partition("-")
    assert prefix == "GHPS"
    assert suffix.isdigit() and len(suffix) == 4


def test_unique_slug_deduplicates(django_db_setup, django_db_blocker):
    from apps.tenants.models import Client

    with django_db_blocker.unblock():
        Client.objects.filter(slug="acme").delete()
        Client(schema_name="acme_x", name="Acme", slug="acme", code="ACM-0001").save()
        assert _unique_slug("Acme") == "acme-2"
