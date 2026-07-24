"""Teacher validation — phone uniqueness (item #8)."""

import pytest

from apps.staff.models import Teacher
from apps.staff.serializers import TeacherSerializer

pytestmark = [pytest.mark.django_db]


def test_duplicate_phone_rejected(tenant_ctx):
    Teacher.objects.create(employee_id="EMP-1", first_name="Ada", phone="9876543210")
    s = TeacherSerializer(data={"first_name": "Grace", "phone": "9876543210"})
    assert not s.is_valid()
    assert "phone" in s.errors


def test_blank_phone_allowed_for_many(tenant_ctx):
    Teacher.objects.create(employee_id="EMP-1", first_name="Ada", phone="")
    s = TeacherSerializer(data={"first_name": "Grace", "phone": ""})
    assert s.is_valid(), s.errors


def test_same_teacher_keeps_its_phone_on_update(tenant_ctx):
    t = Teacher.objects.create(employee_id="EMP-1", first_name="Ada", phone="9876543210")
    s = TeacherSerializer(
        instance=t, data={"first_name": "Ada", "phone": "9876543210"}, partial=True
    )
    assert s.is_valid(), s.errors
