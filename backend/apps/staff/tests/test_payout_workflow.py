"""Payout net math + one-step paid/rejected transitions (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.core.services import InvalidTransition
from apps.staff.models import PayoutStatus, Teacher
from apps.staff.services import compute_net, create_payout, transition_payout

pytestmark = [pytest.mark.django_db]


def _teacher():
    return Teacher.objects.create(employee_id="EMP-1", first_name="Grace", last_name="Hopper")


def test_net_is_base_plus_bonus_minus_deductions():
    assert compute_net("5000.00", "500.00", "250.00") == Decimal("5250.00")


def test_submitted_can_be_paid_directly(tenant_ctx):
    """No HOD/Finance stages — a submitted payout is marked paid in one step."""
    payout = create_payout(teacher=_teacher(), base_amount="5000", pay_period="2024-07")
    assert payout.status == PayoutStatus.SUBMITTED

    payout = transition_payout(payout=payout, to_status=PayoutStatus.PROCESSED)

    assert payout.status == PayoutStatus.PROCESSED
    assert payout.approvals.count() == 1


def test_submitted_can_be_rejected(tenant_ctx):
    payout = create_payout(teacher=_teacher(), base_amount="5000", pay_period="2024-07")
    payout = transition_payout(payout=payout, to_status=PayoutStatus.REJECTED)
    assert payout.status == PayoutStatus.REJECTED


def test_processed_is_terminal(tenant_ctx):
    payout = create_payout(teacher=_teacher(), base_amount="5000", pay_period="2024-07")
    transition_payout(payout=payout, to_status=PayoutStatus.PROCESSED)
    with pytest.raises(InvalidTransition):
        transition_payout(payout=payout, to_status=PayoutStatus.REJECTED)
