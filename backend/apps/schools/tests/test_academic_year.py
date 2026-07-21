"""Academic-year 'exactly one current' invariant (set-as-current)."""

from datetime import date

import pytest

from apps.schools.models import AcademicYear
from apps.schools.views import AcademicYearViewSet

pytestmark = [pytest.mark.django_db]


def _year(label, start_year, is_current=False):
    return AcademicYear.objects.create(
        label=label,
        start_date=date(start_year, 6, 1),
        end_date=date(start_year + 1, 4, 30),
        is_current=is_current,
    )


def test_sync_current_unsets_other_years(tenant_ctx):
    """Marking a year current (create/update path) clears the previous one."""
    old = _year("2023-2024", 2023, is_current=True)
    new = _year("2024-2025", 2024)

    new.is_current = True
    new.save(update_fields=["is_current"])
    AcademicYearViewSet()._sync_current(new)

    old.refresh_from_db()
    new.refresh_from_db()
    assert new.is_current is True
    assert old.is_current is False
    assert AcademicYear.objects.filter(is_current=True).count() == 1


def test_set_current_action_switches_current(tenant_ctx):
    """The set-current action promotes a year and demotes the incumbent."""
    old = _year("2023-2024", 2023, is_current=True)
    target = _year("2024-2025", 2024)

    view = AcademicYearViewSet()
    view.get_object = lambda: target  # type: ignore[method-assign]
    view.get_serializer = lambda obj: type("S", (), {"data": {"id": obj.id}})()  # type: ignore[method-assign]

    view.set_current(request=None, pk=target.id)

    old.refresh_from_db()
    target.refresh_from_db()
    assert target.is_current is True
    assert old.is_current is False
