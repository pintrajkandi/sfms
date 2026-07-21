"""Student form rules: optional email, 10-digit phone (CLAUDE.md §8)."""

import pytest

from apps.students.serializers import StudentSerializer

pytestmark = [pytest.mark.django_db]


def test_email_is_optional(tenant_ctx):
    s = StudentSerializer(data={"first_name": "Ada", "last_name": "L"})
    assert s.is_valid(), s.errors  # no email required


def test_phone_must_be_ten_digits(tenant_ctx):
    s = StudentSerializer(data={"first_name": "A", "last_name": "B", "phone": "12345"})
    assert not s.is_valid()
    assert "phone" in s.errors


def test_phone_strips_formatting_to_ten_digits(tenant_ctx):
    s = StudentSerializer(
        data={"first_name": "A", "last_name": "B", "guardian_phone": "98765-43210"}
    )
    assert s.is_valid(), s.errors
    assert s.validated_data["guardian_phone"] == "9876543210"


def test_blank_phone_allowed(tenant_ctx):
    s = StudentSerializer(data={"first_name": "A", "last_name": "B", "phone": ""})
    assert s.is_valid(), s.errors
