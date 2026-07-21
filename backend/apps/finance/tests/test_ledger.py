"""Double-entry engine: balanced posting + Trial Balance / P&L / Balance Sheet."""

from datetime import date

import pytest

from apps.core.services import ServiceError
from apps.finance import statements
from apps.finance.ledger import post_journal, seed_chart_of_accounts
from apps.finance.models import Account, JournalEntry

pytestmark = [pytest.mark.django_db]


def test_seed_chart_of_accounts_is_idempotent(tenant_ctx):
    first = seed_chart_of_accounts()
    second = seed_chart_of_accounts()
    assert first == 15
    assert second == 0
    assert Account.objects.filter(is_system=True).count() == 15


def test_post_journal_rejects_unbalanced(tenant_ctx):
    seed_chart_of_accounts()
    with pytest.raises(ServiceError):
        post_journal(
            date=date.today(),
            lines=[
                {"account": "1010", "debit": 100, "credit": 0},
                {"account": "4000", "debit": 0, "credit": 90},
            ],
        )


def test_post_journal_is_idempotent_per_source(tenant_ctx):
    seed_chart_of_accounts()
    lines = [
        {"account": "1010", "debit": 500, "credit": 0},
        {"account": "4000", "debit": 0, "credit": 500},
    ]
    e1 = post_journal(date=date.today(), source_type="payment", source_id=1, lines=lines)
    e2 = post_journal(date=date.today(), source_type="payment", source_id=1, lines=lines)
    assert e1.pk == e2.pk
    assert JournalEntry.objects.count() == 1


def test_statements_reconcile(tenant_ctx):
    seed_chart_of_accounts()
    # Collect 10,000 fee into bank; pay 3,000 salary from bank.
    post_journal(
        date=date.today(),
        narration="Fee",
        lines=[
            {"account": "1010", "debit": 10000, "credit": 0},
            {"account": "4000", "debit": 0, "credit": 10000},
        ],
    )
    post_journal(
        date=date.today(),
        narration="Salary",
        lines=[
            {"account": "5000", "debit": 3000, "credit": 0},
            {"account": "1010", "debit": 0, "credit": 3000},
        ],
    )

    tb = statements.trial_balance()
    assert tb["balanced"] is True
    assert tb["total_debit"] == tb["total_credit"]

    pl = statements.profit_and_loss()
    assert pl["total_income"] == "10000.00"
    assert pl["total_expense"] == "3000.00"
    assert pl["net_profit"] == "7000.00"

    bs = statements.balance_sheet()
    # Bank = 7,000; equity = retained earnings 7,000.
    assert bs["total_assets"] == "7000.00"
    assert bs["balanced"] is True
