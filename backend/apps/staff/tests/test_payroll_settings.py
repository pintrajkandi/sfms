"""Per-tenant payroll rates come from SchoolSettings, overriding env defaults."""

from decimal import Decimal

import pytest

from apps.staff.services import compute_statutory

pytestmark = [pytest.mark.django_db]


def test_falls_back_to_env_without_settings(settings, tenant_ctx):
    settings.PAYROLL_PF_RATE = "0.12"
    settings.PAYROLL_PF_WAGE_CEILING = "15000"
    settings.PAYROLL_ESI_WAGE_THRESHOLD = "21000"
    settings.PAYROLL_PROFESSIONAL_TAX = "200"
    stat = compute_statutory(basic="30000", gross="40000")
    assert stat["pf"] == Decimal("1800.00")  # 12% of 15000 ceiling
    assert stat["professional_tax"] == Decimal("200.00")


def test_school_settings_override_env(tenant_ctx):
    from apps.schools.models import SchoolSettings

    SchoolSettings.objects.create(
        name="Demo",
        payroll_pf_rate=Decimal("0.10"),
        payroll_pf_ceiling=Decimal("20000"),
        payroll_esi_rate=Decimal("0.0075"),
        payroll_esi_threshold=Decimal("21000"),
        payroll_professional_tax=Decimal("150"),
    )
    # PF now 10% of min(basic, 20000) = 10% of 20000 = 2000; PT = 150
    stat = compute_statutory(basic="30000", gross="40000")
    assert stat["pf"] == Decimal("2000.00")
    assert stat["professional_tax"] == Decimal("150.00")
