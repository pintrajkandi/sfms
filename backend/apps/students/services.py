"""Student services — id generation and search-vector maintenance."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.logging import ctx, get_logger
from apps.core.search import update_search_vector

from .models import Student

log = get_logger("students")

_SEARCH_FIELDS = {
    "first_name": "A",
    "last_name": "A",
    "student_id": "A",
    "guardian_name": "B",
    "email": "C",
}


def refresh_search_vector(student: Student) -> None:
    update_search_vector(student, _SEARCH_FIELDS)


def next_student_id() -> str:
    year = timezone.now().year
    prefix = f"STU-{year}-"
    last = (
        Student.objects.filter(student_id__startswith=prefix)
        .order_by("-student_id")
        .values_list("student_id", flat=True)
        .first()
    )
    seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{seq:03d}"


_IMPORT_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "gender",
    "date_of_birth",
    "nationality",
    "grade",
    "section",
    "program",
    "guardian_name",
    "guardian_relation",
    "guardian_phone",
    "guardian_email",
    "student_id",
]


def import_template_rows() -> tuple[list[str], list[list[str]]]:
    """Headers + one example row for the downloadable import template."""
    example = [
        "Emma",
        "Johnson",
        "emma@example.com",
        "+1 555 0100",
        "female",
        "2010-05-01",
        "American",
        "Grade 9",
        "A",
        "Science",
        "Robert Johnson",
        "father",
        "+1 555 0101",
        "robert@example.com",
        "",
    ]
    return _IMPORT_FIELDS, [example]


def bulk_import_students(csv_text: str, *, actor=None) -> dict:
    """Parse a CSV and create students row by row; report per-row errors."""
    import csv
    import io

    reader = csv.DictReader(io.StringIO(csv_text))
    created, errors = 0, []
    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        fields = {f: row[f] for f in _IMPORT_FIELDS if row.get(f)}
        if not fields.get("first_name"):
            errors.append({"row": i, "error": "first_name is required"})
            continue
        if fields.get("email") and Student.objects.filter(email__iexact=fields["email"]).exists():
            errors.append({"row": i, "error": f"email {fields['email']} already exists"})
            continue
        try:
            create_student(actor=actor, **fields)
            created += 1
        except Exception as exc:  # bad date, duplicate id, etc.
            errors.append({"row": i, "error": str(exc)[:160]})

    log.info(
        "students imported created=%s errors=%s",
        created,
        len(errors),
        **ctx(user=getattr(actor, "id", "-"), action="import_students"),
    )
    return {"created": created, "error_count": len(errors), "errors": errors[:50]}


@transaction.atomic
def create_student(*, actor=None, **fields) -> Student:
    if not fields.get("student_id"):
        fields["student_id"] = next_student_id()
    student = Student.objects.create(**fields)
    refresh_search_vector(student)
    log.info(
        "student enrolled id=%s",
        student.student_id,
        **ctx(user=getattr(actor, "id", "-"), entity=student.id, action="enroll_student"),
    )
    return student
