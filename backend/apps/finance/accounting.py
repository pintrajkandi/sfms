"""
Accounting sync — export income/expense to Tally, Zoho Books & QuickBooks.

Tally consumes an XML voucher bank; Zoho Books and QuickBooks import CSV. These
build the payload from Payments (income) and Expenses (spend) over a date range.
Live API push (Zoho/QuickBooks OAuth) is out of scope here — the deliverable is
a correct, import-ready file, which is how most schools actually move data.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from xml.sax.saxutils import escape

from apps.collections.models import Payment
from apps.core.logging import ctx, get_logger
from apps.expenses.models import Expense

log = get_logger("finance.accounting")

TARGETS = ("tally", "zoho", "quickbooks")


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def _payments(since: date, until: date):
    return (
        Payment.objects.filter(
            paid_at__date__gte=since, paid_at__date__lte=until, status=Payment.Status.RECORDED
        )
        .select_related("invoice__student")
        .order_by("paid_at")
    )


def _expenses(since: date, until: date):
    return Expense.objects.filter(expense_date__gte=since, expense_date__lte=until).order_by(
        "expense_date"
    )


# --------------------------------------------------------------------------- #
# Tally (XML vouchers).
# --------------------------------------------------------------------------- #
def _voucher(vtype: str, dt: date, party: str, ledger: str, amount: str, narration: str) -> str:
    party, ledger, narration = (escape(x) for x in (party, ledger, narration))
    # Receipt: debit bank, credit party. Payment: credit bank, debit ledger.
    sign = "-" if vtype == "Receipt" else ""
    opp = "" if vtype == "Receipt" else "-"
    return (
        f'<VOUCHER VCHTYPE="{vtype}" ACTION="Create">'
        f"<DATE>{dt:%Y%m%d}</DATE>"
        f"<VOUCHERTYPENAME>{vtype}</VOUCHERTYPENAME>"
        f"<NARRATION>{narration}</NARRATION>"
        f"<ALLLEDGERENTRIES.LIST><LEDGERNAME>{party}</LEDGERNAME>"
        f"<ISDEEMEDPOSITIVE>{'Yes' if vtype == 'Receipt' else 'No'}</ISDEEMEDPOSITIVE>"
        f"<AMOUNT>{sign}{amount}</AMOUNT></ALLLEDGERENTRIES.LIST>"
        f"<ALLLEDGERENTRIES.LIST><LEDGERNAME>{ledger}</LEDGERNAME>"
        f"<ISDEEMEDPOSITIVE>{'No' if vtype == 'Receipt' else 'Yes'}</ISDEEMEDPOSITIVE>"
        f"<AMOUNT>{opp}{amount}</AMOUNT></ALLLEDGERENTRIES.LIST>"
        f"</VOUCHER>"
    )


def tally_xml(since: date, until: date) -> str:
    vouchers = []
    for p in _payments(since, until):
        vouchers.append(
            _voucher(
                "Receipt",
                p.paid_at.date(),
                getattr(p.invoice.student, "full_name", "Student"),
                "Fee Income",
                _q(p.amount),
                f"Fee receipt {p.invoice.invoice_number}",
            )
        )
    for e in _expenses(since, until):
        vouchers.append(
            _voucher(
                "Payment",
                e.expense_date,
                e.get_category_display(),
                "Bank",
                _q(e.amount),
                e.title,
            )
        )
    body = "".join(f'<TALLYMESSAGE xmlns:UDF="TallyUDF">{v}</TALLYMESSAGE>' for v in vouchers)
    return (
        "<ENVELOPE><HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>"
        "<BODY><IMPORTDATA><REQUESTDESC><REPORTNAME>Vouchers</REPORTNAME></REQUESTDESC>"
        f"<REQUESTDATA>{body}</REQUESTDATA></IMPORTDATA></BODY></ENVELOPE>"
    )


# --------------------------------------------------------------------------- #
# Zoho Books & QuickBooks (CSV rows).
# --------------------------------------------------------------------------- #
def zoho_rows(since: date, until: date) -> tuple[list[str], list[list]]:
    headers = [
        "Payment Number",
        "Date",
        "Customer Name",
        "Amount",
        "Payment Mode",
        "Reference Number",
        "Invoice Number",
    ]
    rows = [
        [
            f"PAY-{p.id}",
            p.paid_at.date().isoformat(),
            getattr(p.invoice.student, "full_name", "Student"),
            _q(p.amount),
            p.method,
            p.reference,
            p.invoice.invoice_number,
        ]
        for p in _payments(since, until)
    ]
    return headers, rows


def quickbooks_rows(since: date, until: date) -> tuple[list[str], list[list]]:
    # 3-column bank CSV: credits positive (income), debits negative (expense).
    headers = ["Date", "Description", "Amount"]
    rows = []
    for p in _payments(since, until):
        rows.append(
            [
                p.paid_at.date().isoformat(),
                f"Fee {p.invoice.invoice_number} — {getattr(p.invoice.student, 'full_name', '')}",
                _q(p.amount),
            ]
        )
    for e in _expenses(since, until):
        rows.append([e.expense_date.isoformat(), e.title, f"-{_q(e.amount)}"])
    rows.sort(key=lambda r: r[0])
    return headers, rows


def build_export(target: str, since: date, until: date):
    """Return (kind, filename, payload) where kind is 'xml' or ('csv', headers, rows)."""
    log.info(
        "accounting export target=%s from=%s to=%s",
        target,
        since,
        until,
        **ctx(action="accounting_export"),
    )
    if target == "tally":
        return "xml", "tally_vouchers", tally_xml(since, until)
    if target == "zoho":
        headers, rows = zoho_rows(since, until)
        return "csv", "zoho_payments", (headers, rows)
    headers, rows = quickbooks_rows(since, until)
    return "csv", "quickbooks_transactions", (headers, rows)
