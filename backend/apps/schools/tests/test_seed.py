"""Onboarding default-data seed is correct + idempotent."""

import pytest

from apps.schools.models import Department, SchoolClass, Section
from apps.schools.seed import (
    DEFAULT_CLASSES,
    DEFAULT_DEPARTMENTS,
    DEFAULT_SECTIONS,
    seed_default_setup,
)

pytestmark = [pytest.mark.django_db]


def test_seed_creates_defaults(tenant_ctx):
    seed_default_setup()
    assert Department.objects.count() == len(DEFAULT_DEPARTMENTS)
    assert SchoolClass.objects.count() == len(DEFAULT_CLASSES)
    assert Section.objects.count() == len(DEFAULT_CLASSES) * len(DEFAULT_SECTIONS)


def test_seed_is_idempotent(tenant_ctx):
    seed_default_setup()
    seed_default_setup()
    assert Department.objects.count() == len(DEFAULT_DEPARTMENTS)
    assert SchoolClass.objects.count() == len(DEFAULT_CLASSES)
    assert Section.objects.count() == len(DEFAULT_CLASSES) * len(DEFAULT_SECTIONS)
