"""
Student & Parent fee ledgers — a running statement of what was billed vs paid.

Debits increase what is owed (invoices, refunds); credits reduce it (payments).
The closing balance is the student's / family's outstanding amount.
"""

from __future__ import annotations

from decimal import Decimal

from apps.core.models import ZERO

from .models import InvoiceStatus


def _q(v) -> str:
    return str(Decimal(v or 0).quantize(Decimal("0.01")))


def _events_for(student, *, with_name=False):
    """Chronological (datetime, row) tuples of invoices/payments/refunds."""
    rows = []
    name = student.full_name
    invoices = student.invoices.exclude(status=InvoiceStatus.CANCELLED).prefetch_related(
        "payments", "refunds"
    )
    for inv in invoices:
        base = {"student": name} if with_name else {}
        rows.append(
            (
                inv.created_at,
                {
                    **base,
                    "date": inv.created_at.date().isoformat(),
                    "particulars": f"Invoice {inv.invoice_number}",
                    "type": "invoice",
                    "debit": inv.total,
                    "credit": ZERO,
                },
            )
        )
        for p in inv.payments.all():
            rows.append(
                (
                    p.paid_at,
                    {
                        **base,
                        "date": p.paid_at.date().isoformat(),
                        "particulars": f"Payment · {p.method}"
                        + (f" ({p.reference})" if p.reference else ""),
                        "type": "payment",
                        "debit": ZERO,
                        "credit": p.amount,
                    },
                )
            )
        for r in inv.refunds.all():
            rows.append(
                (
                    r.created_at,
                    {
                        **base,
                        "date": r.created_at.date().isoformat(),
                        "particulars": f"Refund · {r.method}",
                        "type": "refund",
                        "debit": r.amount,
                        "credit": ZERO,
                    },
                )
            )
    return rows


def _finalize(rows):
    """Sort by time, compute running balance + totals."""
    rows.sort(key=lambda t: t[0])
    running = ZERO
    total_debit = total_credit = ZERO
    lines = []
    for _, row in rows:
        running += row["debit"] - row["credit"]
        total_debit += row["debit"]
        total_credit += row["credit"]
        out = {
            **row,
            "debit": _q(row["debit"]),
            "credit": _q(row["credit"]),
            "balance": _q(running),
        }
        lines.append(out)
    return lines, total_debit, total_credit, running


def student_ledger(*, student) -> dict:
    lines, total_debit, total_credit, running = _finalize(_events_for(student))
    return {
        "student": {
            "id": student.id,
            "name": student.full_name,
            "student_id": student.student_id,
            "grade": student.grade,
            "section": student.section,
            "guardian_name": student.guardian_name,
            "guardian_phone": student.guardian_phone,
        },
        "lines": lines,
        "total_billed": _q(total_debit),
        "total_paid": _q(total_credit),
        "outstanding": _q(running),
    }


def parent_ledger(*, students, guardian_name="", guardian_phone="") -> dict:
    """Combined ledger across a guardian's children (siblings)."""
    rows = []
    kids = []
    for s in students:
        rows.extend(_events_for(s, with_name=True))
        kids.append({"id": s.id, "name": s.full_name, "student_id": s.student_id, "grade": s.grade})
    lines, total_debit, total_credit, running = _finalize(rows)
    return {
        "guardian": {"name": guardian_name, "phone": guardian_phone},
        "students": kids,
        "lines": lines,
        "total_billed": _q(total_debit),
        "total_paid": _q(total_credit),
        "outstanding": _q(running),
    }
