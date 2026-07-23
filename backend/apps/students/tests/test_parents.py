"""Parent as a first-class record with children (siblings)."""

import pytest

from apps.students.models import Parent
from apps.students.serializers import ParentSerializer

pytestmark = [pytest.mark.django_db]


def _student(parent=None, **kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Kid")
    kw.setdefault("last_name", "One")
    s = create_student(**kw)
    if parent:
        s.parent = parent
        s.save(update_fields=["parent"])
    return s


def test_parent_groups_children(tenant_ctx):
    parent = Parent.objects.create(name="Ravi Kumar", relation="Father", phone="9876543210")
    _student(parent, first_name="A")
    _student(parent, first_name="B")
    _student(first_name="C")  # unrelated

    data = ParentSerializer(parent).data
    assert data["name"] == "Ravi Kumar"
    assert len(data["children"]) == 2
    assert {c["name"] for c in data["children"]} == {"A One", "B One"}
