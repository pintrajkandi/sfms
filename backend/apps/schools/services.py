"""
Academic-year rollover (CLAUDE.md roadmap).

Orchestrates the start-of-year workflow: clone the fee structure into the new
year (optionally uplifting amounts), promote students up their grades, and make
the new year current. Each sub-step is an audited service in its own app; this
just sequences them in one transaction.
"""

from __future__ import annotations

from django.db import transaction

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger

from .models import AcademicYear

log = get_logger("schools")


@transaction.atomic
def rollover_academic_year(
    *,
    source_year: AcademicYear,
    target_year: AcademicYear,
    grade_map: dict | None = None,
    graduating_grades=None,
    fee_increase_percent=0,
    promote: bool = True,
    clone_fees: bool = True,
    make_current: bool = True,
    actor=None,
) -> dict:
    """Clone fees + promote students + set the new year current. Returns a summary."""
    from apps.fees.services import clone_fee_plans
    from apps.students.services import promote_students

    summary: dict = {
        "source": source_year.label,
        "target": target_year.label,
        "fee_plans_cloned": 0,
        "promoted": 0,
        "graduated": 0,
        "made_current": False,
    }

    if clone_fees:
        summary["fee_plans_cloned"] = clone_fee_plans(
            source_year=source_year,
            target_year=target_year,
            increase_percent=fee_increase_percent,
            actor=actor,
        )

    if promote:
        result = promote_students(
            source_year=source_year,
            target_year=target_year,
            grade_map=grade_map,
            graduating_grades=graduating_grades,
            actor=actor,
        )
        summary["promoted"] = result["promoted"]
        summary["graduated"] = result["graduated"]

    if make_current:
        AcademicYear.objects.filter(is_current=True).exclude(pk=target_year.pk).update(
            is_current=False
        )
        if not target_year.is_current:
            target_year.is_current = True
            target_year.save(update_fields=["is_current", "updated_at"])
        summary["made_current"] = True

    log.info(
        "academic year rollover source=%s target=%s summary=%s",
        source_year.label,
        target_year.label,
        summary,
        **ctx(user=getattr(actor, "id", "-"), entity=target_year.pk, action="rollover_year"),
    )
    record_audit(
        action="academic_year.rollover",
        entity=target_year,
        summary=(
            f"Rollover {source_year.label} → {target_year.label}: "
            f"{summary['fee_plans_cloned']} fees, {summary['promoted']} promoted, "
            f"{summary['graduated']} graduated"
        ),
        actor=actor,
    )
    return summary
