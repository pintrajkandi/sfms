"""Discount / concession resolution + invoice integration (CLAUDE.md §8)."""

from decimal import Decimal

import pytest

from apps.fees.models import DiscountRule, FeeCategory, FeeType, StudentDiscount
from apps.fees.services import has_sibling, resolve_discounts

pytestmark = [pytest.mark.django_db]


def _student(**kw):
    from apps.students.services import create_student

    kw.setdefault("first_name", "Ada")
    kw.setdefault("last_name", "Lovelace")
    return create_student(**kw)


def _fee_type(name="Tuition", amount="1000.00"):
    cat, _ = FeeCategory.objects.get_or_create(name="Academic")
    return FeeType.objects.create(name=name, category=cat, default_amount=amount)


def test_percentage_award_on_whole_subtotal(tenant_ctx):
    student = _student()
    rule = DiscountRule.objects.create(
        name="Merit 25%", code="MERIT25", kind="merit", method="percentage", value="25.00"
    )
    StudentDiscount.objects.create(student=student, rule=rule)

    total, applied = resolve_discounts(student, subtotal=Decimal("1000.00"))
    assert total == Decimal("250.00")
    assert applied[0].code == "MERIT25"


def test_fixed_award_capped_at_max_amount(tenant_ctx):
    student = _student()
    rule = DiscountRule.objects.create(
        name="Flat", code="FLAT", method="fixed", value="500.00", max_amount="300.00"
    )
    StudentDiscount.objects.create(student=student, rule=rule)

    total, _ = resolve_discounts(student, subtotal=Decimal("1000.00"))
    assert total == Decimal("300.00")  # capped by max_amount


def test_fee_type_scoped_rule_only_bites_its_lines(tenant_ctx):
    student = _student()
    transport = _fee_type(name="Transport", amount="200.00")
    rule = DiscountRule.objects.create(
        name="Transport waiver",
        code="TRANSPORT",
        method="percentage",
        value="50.00",
        fee_type=transport,
    )
    StudentDiscount.objects.create(student=student, rule=rule)

    # subtotal 1200 (1000 tuition + 200 transport); rule applies to transport only.
    total, _ = resolve_discounts(
        student, subtotal=Decimal("1200.00"), by_fee_type={transport.id: Decimal("200.00")}
    )
    assert total == Decimal("100.00")  # 50% of 200


def test_non_stackable_takes_single_best(tenant_ctx):
    student = _student()
    small = DiscountRule.objects.create(
        name="Small", code="S", method="percentage", value="10.00", stackable=False
    )
    big = DiscountRule.objects.create(
        name="Big", code="B", method="percentage", value="30.00", stackable=False
    )
    StudentDiscount.objects.create(student=student, rule=small)
    StudentDiscount.objects.create(student=student, rule=big)

    total, applied = resolve_discounts(student, subtotal=Decimal("1000.00"))
    assert total == Decimal("300.00")  # only the best non-stackable applies
    assert len(applied) == 1


def test_stackable_rules_sum(tenant_ctx):
    student = _student()
    a = DiscountRule.objects.create(name="A", code="A", method="percentage", value="10.00")
    b = DiscountRule.objects.create(name="B", code="B", method="fixed", value="50.00")
    StudentDiscount.objects.create(student=student, rule=a)
    StudentDiscount.objects.create(student=student, rule=b)

    total, _ = resolve_discounts(student, subtotal=Decimal("1000.00"))
    assert total == Decimal("150.00")  # 100 + 50


def test_total_capped_at_subtotal(tenant_ctx):
    student = _student()
    rule = DiscountRule.objects.create(
        name="Full ride", code="FULL", method="fixed", value="5000.00"
    )
    StudentDiscount.objects.create(student=student, rule=rule)

    total, _ = resolve_discounts(student, subtotal=Decimal("1000.00"))
    assert total == Decimal("1000.00")  # never more than the bill


def test_sibling_auto_rule_applies_only_with_a_sibling(tenant_ctx):
    DiscountRule.objects.create(
        name="Sibling 10%",
        code="SIB10",
        kind="sibling",
        method="percentage",
        value="10.00",
        auto_apply=True,
    )
    solo = _student(guardian_phone="+91 90000 00001")
    total, applied = resolve_discounts(solo, subtotal=Decimal("1000.00"))
    assert total == Decimal("0.00")
    assert not has_sibling(solo)

    # Second child of the same guardian → both now qualify.
    sib = _student(guardian_phone="+91 90000 00001")
    assert has_sibling(sib)
    total, applied = resolve_discounts(sib, subtotal=Decimal("1000.00"))
    assert total == Decimal("100.00")
    assert applied[0].kind == "sibling"


def test_create_invoice_applies_rules_and_records_audit(tenant_ctx):
    from apps.collections.models import AppliedDiscount
    from apps.collections.services import create_invoice

    student = _student()
    ft = _fee_type()
    rule = DiscountRule.objects.create(
        name="Scholar 20%", code="SCH20", kind="scholarship", method="percentage", value="20.00"
    )
    StudentDiscount.objects.create(student=student, rule=rule)

    inv = create_invoice(student=student, lines=[{"fee_type": ft, "unit_price": "1000.00"}])
    assert inv.discount_amount == Decimal("200.00")
    assert inv.total == Decimal("800.00")
    audit = AppliedDiscount.objects.filter(invoice=inv)
    assert audit.count() == 1
    assert audit.first().code == "SCH20"


def test_explicit_discount_amount_overrides_rules(tenant_ctx):
    from apps.collections.services import create_invoice

    student = _student()
    ft = _fee_type()
    DiscountRule.objects.create(
        name="Scholar 20%", code="SCH20", method="percentage", value="20.00"
    )
    StudentDiscount.objects.create(
        student=student,
        rule=DiscountRule.objects.get(code="SCH20"),
    )
    inv = create_invoice(
        student=student,
        lines=[{"fee_type": ft, "unit_price": "1000.00"}],
        discount_amount="50.00",
    )
    assert inv.discount_amount == Decimal("50.00")  # explicit wins; rules skipped
    assert inv.total == Decimal("950.00")
