"""Bulk CSV import (CLAUDE.md §8)."""
import pytest

from apps.students.models import Student
from apps.students.services import bulk_import_students

pytestmark = [pytest.mark.django_db]


def test_bulk_import_creates_and_reports_errors(tenant_ctx):
    csv_text = (
        "first_name,last_name,email,grade\n"
        "Emma,Johnson,emma@example.com,Grade 9\n"
        "Liam,Smith,liam@example.com,Grade 8\n"
        ",NoFirst,x@example.com,Grade 7\n"  # missing first_name -> error
    )
    result = bulk_import_students(csv_text)
    assert result["created"] == 2
    assert result["error_count"] == 1
    assert Student.objects.filter(email="emma@example.com").exists()


def test_bulk_import_skips_duplicate_email(tenant_ctx):
    Student.objects.create(student_id="STU-X", first_name="Dup", email="dup@example.com")
    result = bulk_import_students("first_name,email\nNew,dup@example.com\n")
    assert result["created"] == 0
    assert result["error_count"] == 1
