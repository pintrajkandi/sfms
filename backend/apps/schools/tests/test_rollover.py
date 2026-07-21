"""Academic-year rollover: clone fees, promote students, set current."""

from datetime import date
from decimal import Decimal

import pytest

from apps.fees.services import clone_fee_plans
from apps.schools.services import rollover_academic_year
from apps.students.services import promote_students

pytestmark = [pytest.mark.django_db]


def _year(label, start_year):
    from apps.schools.models import AcademicYear

    return AcademicYear.objects.create(
        label=label, start_date=date(start_year, 6, 1), end_date=date(start_year + 1, 4, 30)
    )


def _fee_type(name="Tuition"):
    from apps.fees.models import FeeCategory, FeeType

    cat, _ = FeeCategory.objects.get_or_create(name="Academic")
    return FeeType.objects.create(name=name, category=cat, default_amount="1000.00")


def _fee_plan(fee_type, year, grade, amount):
    from apps.fees.models import FeePlan

    return FeePlan.objects.create(fee_type=fee_type, academic_year=year, grade=grade, amount=amount)


def _student(year, grade, **kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(academic_year=year, grade=grade, **kw)


def test_clone_fee_plans_with_increase(tenant_ctx):
    y1, y2 = _year("2025-2026", 2025), _year("2026-2027", 2026)
    ft = _fee_type()
    _fee_plan(ft, y1, "Grade 1", "1000.00")
    _fee_plan(ft, y1, "Grade 2", "1200.00")

    created = clone_fee_plans(source_year=y1, target_year=y2, increase_percent=10)
    assert created == 2
    from apps.fees.models import FeePlan

    g1 = FeePlan.objects.get(academic_year=y2, grade="Grade 1")
    assert g1.amount == Decimal("1100.00")  # +10%


def test_clone_skips_existing(tenant_ctx):
    y1, y2 = _year("2025-2026", 2025), _year("2026-2027", 2026)
    ft = _fee_type()
    _fee_plan(ft, y1, "Grade 1", "1000.00")
    _fee_plan(ft, y2, "Grade 1", "999.00")  # already exists in target
    assert clone_fee_plans(source_year=y1, target_year=y2) == 0


def test_clone_same_year_rejected(tenant_ctx):
    from apps.core.services import ServiceError

    y1 = _year("2025-2026", 2025)
    with pytest.raises(ServiceError):
        clone_fee_plans(source_year=y1, target_year=y1)


def test_promote_students_with_grade_map(tenant_ctx):
    from apps.students.models import EnrollmentStatus

    y1, y2 = _year("2025-2026", 2025), _year("2026-2027", 2026)
    s1 = _student(y1, "Grade 1")
    s2 = _student(y1, "Grade 12")

    result = promote_students(
        source_year=y1,
        target_year=y2,
        grade_map={"Grade 1": "Grade 2"},
        graduating_grades=["Grade 12"],
    )
    assert result == {"promoted": 1, "graduated": 1}
    s1.refresh_from_db()
    s2.refresh_from_db()
    assert s1.grade == "Grade 2"
    assert s1.academic_year_id == y2.id
    assert s2.status == EnrollmentStatus.GRADUATED
    assert s2.academic_year_id == y1.id  # graduates stay put


def test_full_rollover(tenant_ctx):
    y1, y2 = _year("2025-2026", 2025), _year("2026-2027", 2026)
    ft = _fee_type()
    _fee_plan(ft, y1, "Grade 1", "1000.00")
    _student(y1, "Grade 1")

    summary = rollover_academic_year(
        source_year=y1,
        target_year=y2,
        grade_map={"Grade 1": "Grade 2"},
        fee_increase_percent=5,
    )
    assert summary["fee_plans_cloned"] == 1
    assert summary["promoted"] == 1
    assert summary["made_current"] is True
    y2.refresh_from_db()
    assert y2.is_current is True
