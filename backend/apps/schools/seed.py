"""
Default data seeded into a school's schema at onboarding.

`seed_default_setup` creates a starter set of departments, classes and sections
so a freshly onboarded school isn't empty. Everything created here has normal
CRUD endpoints, so an admin can freely keep, edit or delete any of it. The
function is idempotent — safe to call more than once.
"""

from __future__ import annotations

from apps.core.logging import ctx, get_logger

log = get_logger("schools")

DEFAULT_DEPARTMENTS = [
    "Administration",
    "Mathematics",
    "Science",
    "English",
    "Social Studies",
    "Languages",
    "Computer Science",
    "Physical Education",
    "Arts",
]

DEFAULT_CLASSES = [
    "Nursery",
    "LKG",
    "UKG",
    "Grade 1",
    "Grade 2",
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Grade 8",
    "Grade 9",
    "Grade 10",
]

DEFAULT_SECTIONS = ["A", "B"]


def seed_default_setup() -> dict:
    """Idempotently seed departments + classes + sections + chart of accounts."""
    from apps.finance.ledger import seed_chart_of_accounts

    from .models import Department, SchoolClass, Section

    dept_created = 0
    for name in DEFAULT_DEPARTMENTS:
        _, created = Department.objects.get_or_create(name=name)
        dept_created += int(created)

    class_created = 0
    section_created = 0
    for order, name in enumerate(DEFAULT_CLASSES):
        school_class, created = SchoolClass.objects.get_or_create(
            name=name, defaults={"order": order}
        )
        class_created += int(created)
        for section_name in DEFAULT_SECTIONS:
            _, s_created = Section.objects.get_or_create(
                school_class=school_class, name=section_name
            )
            section_created += int(s_created)

    accounts_created = seed_chart_of_accounts()

    summary = {
        "departments": dept_created,
        "classes": class_created,
        "sections": section_created,
        "accounts": accounts_created,
    }
    log.info(
        "seeded default setup departments=%s classes=%s sections=%s accounts=%s",
        dept_created,
        class_created,
        section_created,
        accounts_created,
        **ctx(action="seed_default_setup"),
    )
    return summary
