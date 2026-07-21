"""Staff/team management service (CLAUDE.md §8)."""

import pytest

from apps.accounts.models import Role, User
from apps.accounts.services import create_staff
from apps.core.services import ServiceError

pytestmark = [pytest.mark.django_db]


def test_create_staff_sets_role_and_password(tenant_ctx):
    user = create_staff(
        email="Front@Desk.test",
        first_name="Front",
        last_name="Desk",
        role=Role.FRONT_DESK,
        password="s3cret-pass",
    )
    assert user.email == "front@desk.test"  # normalized
    assert user.username == "front@desk.test"
    assert user.role == Role.FRONT_DESK
    assert user.email_verified is True  # admin-vouched
    assert user.check_password("s3cret-pass")


def test_duplicate_email_rejected(tenant_ctx):
    create_staff(
        email="dup@x.test", first_name="A", last_name="B", role=Role.STAFF, password="pw12345678"
    )
    with pytest.raises(ServiceError):
        create_staff(
            email="DUP@x.test",
            first_name="C",
            last_name="D",
            role=Role.STAFF,
            password="pw12345678",
        )


def test_created_staff_can_authenticate(tenant_ctx):
    from django.contrib.auth import authenticate

    create_staff(
        email="fin@x.test",
        first_name="Fin",
        last_name="Ops",
        role=Role.FINANCE,
        password="pw12345678",
    )
    user = authenticate(username="fin@x.test", password="pw12345678")
    assert user is not None
    assert user.role == Role.FINANCE
    assert User.objects.filter(email="fin@x.test").count() == 1
