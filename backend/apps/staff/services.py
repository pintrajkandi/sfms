"""
Payout money math + guarded approval workflow (CLAUDE.md §5).

Workflow: submitted → hod_approved → finance_approved → processed.
Any stage (except processed) may be rejected. Transitions are role-guarded and
recorded in PayoutApproval; no free-form status writes from the view.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.services import InvalidTransition

from .models import Payout, PayoutApproval, PayoutStatus

log = get_logger("staff")

# Allowed forward transitions.
_ALLOWED = {
    PayoutStatus.SUBMITTED: {PayoutStatus.HOD_APPROVED, PayoutStatus.REJECTED},
    PayoutStatus.HOD_APPROVED: {PayoutStatus.FINANCE_APPROVED, PayoutStatus.REJECTED},
    PayoutStatus.FINANCE_APPROVED: {PayoutStatus.PROCESSED, PayoutStatus.REJECTED},
    PayoutStatus.PROCESSED: set(),
    PayoutStatus.REJECTED: set(),
}

# Which role may perform each transition.
_ROLE_FOR_TARGET = {
    PayoutStatus.HOD_APPROVED: "can_review_payout_hod",
    PayoutStatus.FINANCE_APPROVED: "can_review_payout_finance",
    PayoutStatus.PROCESSED: "can_review_payout_finance",
    PayoutStatus.REJECTED: None,  # any reviewer may reject
}


def _q(v) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"))


def compute_net(base, bonus, deductions) -> Decimal:
    return _q(Decimal(base) + Decimal(bonus) - Decimal(deductions))


@transaction.atomic
def create_payout(
    *,
    teacher,
    base_amount,
    bonus_amount=0,
    deductions=0,
    pay_period: str,
    pay_type="salary",
    currency="USD",
    payment_method="",
    notes="",
    actor=None,
) -> Payout:
    payout = Payout.objects.create(
        teacher=teacher,
        pay_type=pay_type,
        pay_period=pay_period,
        base_amount=_q(base_amount),
        bonus_amount=_q(bonus_amount),
        deductions=_q(deductions),
        net_amount=compute_net(base_amount, bonus_amount, deductions),
        currency=currency,
        payment_method=payment_method,
        notes=notes,
        status=PayoutStatus.SUBMITTED,
    )
    log.info(
        "payout submitted teacher=%s period=%s net=%s",
        teacher.employee_id,
        pay_period,
        payout.net_amount,
        **ctx(user=getattr(actor, "id", "-"), entity=payout.id, action="submit_payout"),
    )
    return payout


@transaction.atomic
def transition_payout(*, payout: Payout, to_status: str, actor=None, note: str = "") -> Payout:
    payout = Payout.objects.select_for_update().get(pk=payout.pk)
    current = PayoutStatus(payout.status)
    target = PayoutStatus(to_status)

    if target not in _ALLOWED[current]:
        raise InvalidTransition(f"Cannot move payout from {current} to {target}.")

    guard = _ROLE_FOR_TARGET.get(target)
    if guard and actor is not None and not getattr(actor, guard, False):
        raise InvalidTransition(f"User lacks permission for transition to {target}.")

    payout.status = target
    payout.save(update_fields=["status", "updated_at"])
    PayoutApproval.objects.create(
        payout=payout,
        from_status=current,
        to_status=target,
        actor=actor if getattr(actor, "pk", None) else None,
        note=note,
    )
    level = log.warning if target == PayoutStatus.REJECTED else log.info
    level(
        "payout %s → %s teacher=%s",
        current,
        target,
        payout.teacher.employee_id,
        **ctx(user=getattr(actor, "id", "-"), entity=payout.id, action="transition_payout"),
    )
    record_audit(
        action="payout.transition",
        entity=payout,
        summary=f"Payout {payout.teacher.employee_id} {current} → {target}",
        changes={"status": [str(current), str(target)]},
        actor=actor,
    )
    return payout
