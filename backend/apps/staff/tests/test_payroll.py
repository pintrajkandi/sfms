"""Statutory payroll (PF/ESI/TDS) + payslip (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.staff.models import PayoutStatus
from apps.staff.services import compute_statutory, payslip_data, run_payroll

pytestmark = [pytest.mark.django_db]


def _teacher(**kw):
    from apps.staff.models import Teacher

    kw.setdefault("employee_id", "EMP-1")
    kw.setdefault("first_name", "Grace")
    kw.setdefault("last_name", "Hopper")
    kw.setdefault("base_salary", "50000.00")
    return Teacher.objects.create(**kw)


def test_pf_is_twelve_percent_of_basic_capped(settings, tenant_ctx):
    settings.PAYROLL_PF_RATE = "0.12"
    settings.PAYROLL_PF_WAGE_CEILING = "15000"
    settings.PAYROLL_ESI_WAGE_THRESHOLD = "21000"
    settings.PAYROLL_PROFESSIONAL_TAX = "200"
    # basic 30000 > ceiling 15000 -> PF on 15000 = 1800
    stat = compute_statutory(basic="30000", gross="40000")
    assert stat["pf"] == Decimal("1800.00")
    # gross 40000 > ESI threshold -> no ESI
    assert stat["esi"] == Decimal("0.00")
    assert stat["professional_tax"] == Decimal("200.00")


def test_esi_applies_below_threshold(settings, tenant_ctx):
    settings.PAYROLL_ESI_EMPLOYEE_RATE = "0.0075"
    settings.PAYROLL_ESI_WAGE_THRESHOLD = "21000"
    stat = compute_statutory(basic="15000", gross="20000")
    assert stat["esi"] == Decimal("150.00")  # 0.75% of 20000


def test_overrides_take_precedence(tenant_ctx):
    stat = compute_statutory(
        basic="30000", gross="40000", pf_override="1000", esi_override="0", pt_override="0"
    )
    assert stat["pf"] == Decimal("1000.00")
    assert stat["professional_tax"] == Decimal("0.00")


def test_run_payroll_computes_gross_and_net(settings, tenant_ctx):
    settings.PAYROLL_PF_RATE = "0.12"
    settings.PAYROLL_PF_WAGE_CEILING = "15000"
    settings.PAYROLL_ESI_WAGE_THRESHOLD = "21000"
    settings.PAYROLL_PROFESSIONAL_TAX = "200"
    teacher = _teacher()

    payout = run_payroll(
        teacher=teacher,
        basic="30000",
        allowances="10000",
        bonus="5000",
        tds="2000",
        pay_period="2026-07",
        currency="INR",
    )
    # gross = 30000 + 10000 + 5000 = 45000
    assert payout.gross_amount == Decimal("45000.00")
    assert payout.pf_amount == Decimal("1800.00")  # 12% of 15000
    assert payout.esi_amount == Decimal("0.00")  # gross > threshold
    assert payout.tds_amount == Decimal("2000.00")
    assert payout.professional_tax == Decimal("200.00")
    # deductions = 1800 + 0 + 200 + 2000 = 4000 ; net = 45000 - 4000 = 41000
    assert payout.deductions == Decimal("4000.00")
    assert payout.net_amount == Decimal("41000.00")
    assert payout.status == PayoutStatus.SUBMITTED


def test_payslip_data_structure(tenant_ctx):
    teacher = _teacher()
    payout = run_payroll(teacher=teacher, basic="20000", pay_period="2026-07")
    slip = payslip_data(payout)
    assert slip["employee_id"] == "EMP-1"
    assert slip["net_amount"] == str(payout.net_amount)
    labels = {d["label"] for d in slip["deductions"]}
    assert "Provident Fund (PF)" in labels and "ESI" in labels and "TDS" in labels
    assert {e["label"] for e in slip["earnings"]} == {"Basic", "Allowances", "Bonus"}
