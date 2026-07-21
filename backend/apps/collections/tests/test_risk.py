"""Predictive-collections risk scoring + AI assistant fallback (CLAUDE.md §8)."""

import datetime

import pytest
from django.utils import timezone

from apps.collections.selectors import collection_risk_report
from apps.collections.services import create_invoice, record_payment

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type():
    from apps.fees.models import FeeCategory, FeeType

    cat, _ = FeeCategory.objects.get_or_create(name="Academic")
    ft, _ = FeeType.objects.get_or_create(
        name="Tuition", defaults={"category": cat, "default_amount": "1000.00"}
    )
    return ft


def _invoice(student, *, days, unit="1000.00"):
    due = timezone.now().date() + datetime.timedelta(days=days)
    return create_invoice(
        student=student, lines=[{"fee_type": _fee_type(), "unit_price": unit}], due_date=due
    )


def test_only_students_with_balance_appear(tenant_ctx):
    paid_student = _student()
    inv = _invoice(paid_student, days=-5)
    record_payment(invoice=inv, amount="1000.00", method="cash", idempotency_key="r-paid")
    # no outstanding -> excluded
    report = collection_risk_report()
    assert report["total_at_risk"] == 0


def test_overdue_student_scores_higher_than_current(tenant_ctx):
    overdue = _student(first_name="Over", last_name="Due")
    _invoice(overdue, days=-90)  # very overdue
    current = _student(first_name="Cur", last_name="Rent")
    _invoice(current, days=15)  # not yet due

    report = collection_risk_report()
    by_name = {r["student"]: r for r in report["at_risk"]}
    assert by_name["Over Due"]["risk_score"] > by_name["Cur Rent"]["risk_score"]
    assert by_name["Over Due"]["risk_band"] in ("medium", "high")
    assert by_name["Over Due"]["days_overdue"] >= 89


def test_report_sorted_desc_and_counts_add_up(tenant_ctx):
    for i in range(3):
        s = _student(first_name=f"S{i}", last_name="X")
        _invoice(s, days=-(i + 1) * 20)
    report = collection_risk_report()
    scores = [r["risk_score"] for r in report["at_risk"]]
    assert scores == sorted(scores, reverse=True)
    assert sum(report["counts"].values()) == report["total_at_risk"]


def test_reasons_and_action_present(tenant_ctx):
    s = _student()
    _invoice(s, days=-40)
    row = collection_risk_report()["at_risk"][0]
    assert row["reasons"]
    assert row["recommended_action"]


# --- assistant fallback (no Claude key) ---


def test_assistant_disabled_returns_rule_based(tenant_ctx, settings):
    from apps.collections.assistant import ask, assistant_enabled

    settings.ANTHROPIC_API_KEY = ""
    assert assistant_enabled() is False

    s = _student()
    _invoice(s, days=-30)
    result = ask("Who is most likely to default?")
    assert result["source"] == "rule-based"
    assert "Outstanding" in result["answer"]
    assert "Risk:" in result["answer"]
