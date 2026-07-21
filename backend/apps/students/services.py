"""Student services — id generation and search-vector maintenance."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.search import update_search_vector

from .models import EnrollmentStatus, Student

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
    "grade",
    "section",
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
        "9876543210",
        "female",
        "2010-05-01",
        "Grade 9",
        "A",
        "Robert Johnson",
        "father",
        "9876543211",
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


@transaction.atomic
def promote_students(
    *,
    source_year,
    target_year,
    grade_map: dict[str, str] | None = None,
    graduating_grades=None,
    actor=None,
) -> dict:
    """
    Advance active students of `source_year` into `target_year`.

    `grade_map` maps old grade → new grade (grades not listed keep their grade).
    Students whose grade is in `graduating_grades` are marked GRADUATED and stay
    in the source year. Returns {promoted, graduated}.
    """
    grade_map = grade_map or {}
    graduating = set(graduating_grades or [])

    students = Student.objects.alive().filter(
        academic_year=source_year, status=EnrollmentStatus.ACTIVE
    )
    promoted = graduated = 0
    for student in students:
        if student.grade in graduating:
            student.status = EnrollmentStatus.GRADUATED
            student.save(update_fields=["status", "updated_at"])
            graduated += 1
            continue
        student.grade = grade_map.get(student.grade, student.grade)
        student.academic_year = target_year
        student.save(update_fields=["grade", "academic_year", "updated_at"])
        promoted += 1

    log.info(
        "students promoted source=%s target=%s promoted=%s graduated=%s",
        source_year.label,
        target_year.label,
        promoted,
        graduated,
        **ctx(user=getattr(actor, "id", "-"), entity=target_year.pk, action="promote_students"),
    )
    record_audit(
        action="students.promoted",
        entity=target_year,
        summary=(
            f"Promoted {promoted}, graduated {graduated}: "
            f"{source_year.label} → {target_year.label}"
        ),
        actor=actor,
    )
    return {"promoted": promoted, "graduated": graduated}
