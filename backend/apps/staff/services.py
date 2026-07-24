"""
Payout money math + guarded approval workflow (CLAUDE.md §5).

Workflow: submitted → hod_approved → finance_approved → processed.
Any stage (except processed) may be rejected. Transitions are role-guarded and
recorded in PayoutApproval; no free-form status writes from the view.
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import transaction

from apps.core.audit import record_audit
from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO
from apps.core.services import InvalidTransition, ServiceError

from .models import Payout, PayoutApproval, PayoutStatus

log = get_logger("staff")


def _ensure_period_not_taken(*, teacher, pay_period: str, pay_type: str) -> None:
    """Block a duplicate payout for the same teacher + month + kind.

    A rejected payout does not count, so a corrected one can be re-submitted for
    the same period.
    """
    clash = (
        Payout.objects.filter(teacher=teacher, pay_period=pay_period, pay_type=pay_type)
        .exclude(status=PayoutStatus.REJECTED)
        .exists()
    )
    if clash:
        raise ServiceError(
            f"A {pay_type} payout for {teacher.full_name} already exists for {pay_period}."
        )


# Allowed transitions. The multi-stage HOD/Finance approval was removed — a
# submitted payout is either paid (processed) or rejected in one step. Legacy
# intermediate statuses remain routable so old rows can still be closed out.
_ALLOWED = {
    PayoutStatus.SUBMITTED: {PayoutStatus.PROCESSED, PayoutStatus.REJECTED},
    PayoutStatus.HOD_APPROVED: {PayoutStatus.PROCESSED, PayoutStatus.REJECTED},
    PayoutStatus.FINANCE_APPROVED: {PayoutStatus.PROCESSED, PayoutStatus.REJECTED},
    PayoutStatus.PROCESSED: set(),
    PayoutStatus.REJECTED: set(),
}

# No per-stage role guards anymore — anyone with payout write access (admin /
# finance / hod, enforced at the viewset) may mark a payout paid or rejected.
_ROLE_FOR_TARGET: dict = {}


def _q(v) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"))


def compute_net(base, bonus, deductions) -> Decimal:
    return _q(Decimal(base) + Decimal(bonus) - Decimal(deductions))


def _payroll_config() -> dict:
    """Per-tenant statutory rates from SchoolSettings, falling back to env."""
    from apps.schools.models import SchoolSettings

    s = SchoolSettings.objects.first()
    if s is not None:
        return {
            "pf_rate": Decimal(s.payroll_pf_rate),
            "pf_ceiling": Decimal(s.payroll_pf_ceiling),
            "esi_rate": Decimal(s.payroll_esi_rate),
            "esi_threshold": Decimal(s.payroll_esi_threshold),
            "pt": Decimal(s.payroll_professional_tax),
        }
    return {
        "pf_rate": Decimal(settings.PAYROLL_PF_RATE),
        "pf_ceiling": Decimal(settings.PAYROLL_PF_WAGE_CEILING),
        "esi_rate": Decimal(settings.PAYROLL_ESI_EMPLOYEE_RATE),
        "esi_threshold": Decimal(settings.PAYROLL_ESI_WAGE_THRESHOLD),
        "pt": Decimal(settings.PAYROLL_PROFESSIONAL_TAX),
    }


def compute_statutory(
    *,
    basic,
    gross,
    tds=0,
    other_deductions=0,
    pf_override=None,
    esi_override=None,
    pt_override=None,
) -> dict:
    """
    Compute statutory deductions from a basic wage + gross pay.

    Rates come from the school's SchoolSettings (env defaults if unset). PF =
    PF_RATE × min(basic, wage ceiling); ESI = ESI_RATE × gross while gross ≤
    threshold (else 0); professional tax is flat. Any component may be overridden.
    """
    basic = Decimal(basic)
    gross = Decimal(gross)
    cfg = _payroll_config()

    if pf_override is not None:
        pf = Decimal(pf_override)
    else:
        pf_base = min(basic, cfg["pf_ceiling"])
        pf = pf_base * cfg["pf_rate"]

    if esi_override is not None:
        esi = Decimal(esi_override)
    elif gross <= cfg["esi_threshold"]:
        esi = gross * cfg["esi_rate"]
    else:
        esi = ZERO

    pt = cfg["pt"] if pt_override is None else Decimal(pt_override)
    tds = Decimal(tds)
    other = Decimal(other_deductions)

    pf, esi, pt, tds, other = (_q(x) for x in (pf, esi, pt, tds, other))
    total = _q(pf + esi + pt + tds + other)
    return {
        "pf": pf,
        "esi": esi,
        "professional_tax": pt,
        "tds": tds,
        "other_deductions": other,
        "total_deductions": total,
    }


@transaction.atomic
def run_payroll(
    *,
    teacher,
    basic,
    allowances=0,
    bonus=0,
    tds=0,
    other_deductions=0,
    pay_period: str,
    currency="INR",
    payment_method="",
    notes="",
    pf_override=None,
    esi_override=None,
    pt_override=None,
    actor=None,
) -> Payout:
    """
    Create a salary Payout with a full statutory breakdown (PF/ESI/TDS/PT).
    gross = basic + allowances + bonus; net = gross − total deductions.
    """
    basic = _q(Decimal(basic))
    allowances = _q(Decimal(allowances))
    bonus = _q(Decimal(bonus))
    gross = _q(basic + allowances + bonus)

    stat = compute_statutory(
        basic=basic,
        gross=gross,
        tds=tds,
        other_deductions=other_deductions,
        pf_override=pf_override,
        esi_override=esi_override,
        pt_override=pt_override,
    )
    net = _q(gross - stat["total_deductions"])

    _ensure_period_not_taken(teacher=teacher, pay_period=pay_period, pay_type=Payout.PayType.SALARY)
    payout = Payout.objects.create(
        teacher=teacher,
        pay_type=Payout.PayType.SALARY,
        pay_period=pay_period,
        base_amount=basic,
        bonus_amount=bonus,
        allowances=allowances,
        gross_amount=gross,
        pf_amount=stat["pf"],
        esi_amount=stat["esi"],
        tds_amount=stat["tds"],
        professional_tax=stat["professional_tax"],
        other_deductions=stat["other_deductions"],
        deductions=stat["total_deductions"],
        net_amount=net,
        currency=currency,
        payment_method=payment_method,
        notes=notes,
        status=PayoutStatus.SUBMITTED,
    )
    log.info(
        "payroll run teacher=%s period=%s gross=%s deductions=%s net=%s",
        teacher.employee_id,
        pay_period,
        gross,
        stat["total_deductions"],
        net,
        **ctx(user=getattr(actor, "id", "-"), entity=payout.id, action="run_payroll"),
    )
    record_audit(
        action="payroll.run",
        entity=payout,
        summary=(
            f"Payroll {teacher.employee_id} {pay_period}: gross {gross}, "
            f"deductions {stat['total_deductions']}, net {net} {currency}"
        ),
        actor=actor,
    )
    return payout


def payslip_data(payout: Payout) -> dict:
    """Structured payslip (earnings + deductions + net) for display / PDF."""
    earnings = [
        {"label": "Basic", "amount": str(payout.base_amount)},
        {"label": "Allowances", "amount": str(payout.allowances)},
        {"label": "Bonus", "amount": str(payout.bonus_amount)},
    ]
    deductions = [
        {"label": "Provident Fund (PF)", "amount": str(payout.pf_amount)},
        {"label": "ESI", "amount": str(payout.esi_amount)},
        {"label": "TDS", "amount": str(payout.tds_amount)},
        {"label": "Professional Tax", "amount": str(payout.professional_tax)},
        {"label": "Other", "amount": str(payout.other_deductions)},
    ]
    return {
        "payout_id": payout.id,
        "employee_id": payout.teacher.employee_id,
        "employee_name": payout.teacher.full_name,
        "pay_period": payout.pay_period,
        "currency": payout.currency,
        "status": payout.status,
        "earnings": earnings,
        "deductions": deductions,
        "gross_amount": str(payout.gross_amount),
        "total_deductions": str(payout.deductions),
        "net_amount": str(payout.net_amount),
    }


@transaction.atomic
def create_payout(
    *,
    teacher,
    base_amount,
    bonus_amount=0,
    deductions=0,
    pay_period: str,
    pay_type="salary",
    currency="INR",
    payment_method="",
    payment_reference="",
    notes="",
    days_present=None,
    days_absent=None,
    deduction_reason="",
    actor=None,
) -> Payout:
    _ensure_period_not_taken(teacher=teacher, pay_period=pay_period, pay_type=pay_type)
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
        payment_reference=payment_reference,
        notes=notes,
        days_present=days_present,
        days_absent=days_absent,
        deduction_reason=deduction_reason,
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
    if target == PayoutStatus.PROCESSED:
        from apps.finance.ledger import _safe, post_payroll

        _safe(post_payroll, payout)
    return payout
