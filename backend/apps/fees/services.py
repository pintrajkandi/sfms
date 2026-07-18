"""
Discount / concession resolution (CLAUDE.md §5 — business logic in services).

`resolve_discounts` turns a student's awarded scholarships/concessions plus any
auto-applied rules (sibling discounts) into a single money figure + an auditable
breakdown, at invoice time. All math is Decimal; nothing is ever stored frozen on
the rule. Stackable rules sum; among non-stackable rules only the single best
applies; the grand total is capped at the invoice subtotal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.core.logging import ctx, get_logger
from apps.core.models import ZERO

from .models import DiscountRule, StudentDiscount

log = get_logger("fees.discounts")

_CENTS = Decimal("0.01")
_HUNDRED = Decimal("100")


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_CENTS)


@dataclass(frozen=True)
class AppliedDiscount:
    """One resolved concession — carries enough to persist an audit row."""

    rule_id: int | None
    code: str
    name: str
    kind: str
    amount: Decimal


def _within(on: date, start, end) -> bool:
    if start and on < start:
        return False
    if end and on > end:
        return False
    return True


def has_sibling(student) -> bool:
    """
    A student has a sibling when another *alive* student shares a non-blank
    guardian phone or guardian email — the practical join schools rely on.
    """
    from apps.students.models import Student

    phone = (student.guardian_phone or "").strip()
    email = (student.guardian_email or "").strip().lower()
    if not (phone or email):
        return False

    others = Student.objects.alive().exclude(pk=student.pk)
    q = None
    if phone:
        q = others.filter(guardian_phone=phone)
    if email:
        by_email = others.filter(guardian_email__iexact=email)
        q = by_email if q is None else (q | by_email)
    return q.exists()


def _rule_qualifies(rule: DiscountRule, student, on: date) -> bool:
    """Auto rules gate on eligibility; sibling rules require an actual sibling."""
    if not _within(on, rule.valid_from, rule.valid_to):
        return False
    if rule.kind == DiscountRule.Kind.SIBLING:
        return has_sibling(student)
    return True


def _candidate_rules(student, on: date) -> dict[int, tuple[DiscountRule, Decimal]]:
    """
    Map rule_id -> (rule, value_to_use). Explicit awards win over auto rules for
    the same rule (an award may override the value).
    """
    candidates: dict[int, tuple[DiscountRule, Decimal]] = {}

    # Auto-applied rules (e.g. sibling) — no award row needed.
    for rule in DiscountRule.objects.alive().filter(is_active=True, auto_apply=True):
        if _rule_qualifies(rule, student, on):
            candidates[rule.id] = (rule, rule.value)

    # Explicit awards override / add.
    awards = StudentDiscount.objects.filter(student=student, is_active=True).select_related("rule")
    for award in awards:
        rule = award.rule
        if rule.deleted_at is not None or not rule.is_active:
            continue
        if not _within(on, award.valid_from, award.valid_to):
            continue
        if not _within(on, rule.valid_from, rule.valid_to):
            continue
        value = award.override_value if award.override_value is not None else rule.value
        candidates[rule.id] = (rule, value)

    return candidates


def _base_amount(rule: DiscountRule, subtotal: Decimal, by_fee_type: dict[int, Decimal]) -> Decimal:
    """The money a rule bites into: its fee type's lines, or the whole subtotal."""
    if rule.fee_type_id:
        return by_fee_type.get(rule.fee_type_id, ZERO)
    return subtotal


def _compute(rule: DiscountRule, value: Decimal, base: Decimal) -> Decimal:
    if base <= ZERO:
        return ZERO
    if rule.method == DiscountRule.Method.PERCENTAGE:
        amount = base * (Decimal(value) / _HUNDRED)
    else:
        amount = Decimal(value)
    amount = min(amount, base)  # never exceed what it applies to
    if rule.max_amount and rule.max_amount > ZERO:
        amount = min(amount, rule.max_amount)
    return _q(max(amount, ZERO))


def resolve_discounts(
    student,
    *,
    subtotal: Decimal,
    by_fee_type: dict[int, Decimal] | None = None,
    on_date: date | None = None,
) -> tuple[Decimal, list[AppliedDiscount]]:
    """
    Resolve all concessions for `student` against a bill.

    `subtotal` is the pre-discount invoice subtotal; `by_fee_type` maps
    fee_type_id -> summed line amount (for fee-type-scoped rules). Returns
    (total_discount, [AppliedDiscount…]); total is capped at `subtotal`.
    """
    subtotal = _q(Decimal(subtotal))
    by_fee_type = by_fee_type or {}
    on = on_date or date.today()

    stackable: list[AppliedDiscount] = []
    non_stackable: list[AppliedDiscount] = []

    for rule, value in _candidate_rules(student, on).values():
        amount = _compute(rule, value, _base_amount(rule, subtotal, by_fee_type))
        if amount <= ZERO:
            continue
        applied = AppliedDiscount(
            rule_id=rule.id, code=rule.code, name=rule.name, kind=rule.kind, amount=amount
        )
        (stackable if rule.stackable else non_stackable).append(applied)

    chosen = list(stackable)
    if non_stackable:
        chosen.append(max(non_stackable, key=lambda a: a.amount))

    total = _q(sum((a.amount for a in chosen), ZERO))
    if total > subtotal:
        # Never discount more than the bill — scale the last-resort cap.
        total = subtotal

    chosen.sort(key=lambda a: a.amount, reverse=True)
    log.info(
        "discounts resolved student=%s count=%s total=%s",
        student.pk,
        len(chosen),
        total,
        **ctx(entity=student.pk, action="resolve_discounts"),
    )
    return total, chosen
