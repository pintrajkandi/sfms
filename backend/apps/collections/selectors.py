"""Read-side aggregations for invoices/payments (student detail, dashboards)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import TruncMonth

from apps.core.models import ZERO

from .models import Invoice, InvoiceLine, InvoiceStatus, Payment


def _q(v: Decimal) -> Decimal:
    return Decimal(v).quantize(Decimal("0.01"))


def student_fee_summary(student) -> dict:
    """Fee breakdown + payment progress + history for the student detail page."""
    invoices = student.invoices.exclude(status=InvoiceStatus.CANCELLED)
    total = invoices.aggregate(s=Sum("total"))["s"] or ZERO
    paid = invoices.aggregate(s=Sum("amount_paid"))["s"] or ZERO
    outstanding = total - paid
    progress = float((paid / total) * 100) if total > ZERO else 0.0

    invoice_rows = [
        {
            "invoice_number": inv.invoice_number,
            "status": inv.status,
            "total": str(inv.total),
            "amount_paid": str(inv.amount_paid),
            "balance": str(inv.balance),
            "due_date": inv.due_date,
        }
        for inv in invoices.order_by("-created_at")
    ]

    # Per-fee-type breakdown — payments are per-invoice, so allocate proportionally.
    agg: dict[str, dict] = {}
    for inv in invoices.prefetch_related("lines__fee_type__category"):
        ratio = (inv.amount_paid / inv.total) if inv.total > ZERO else Decimal(0)
        for line in inv.lines.all():
            row = agg.setdefault(
                line.fee_type.name,
                {
                    "fee_type": line.fee_type.name,
                    "category": getattr(line.fee_type.category, "name", ""),
                    "amount": ZERO,
                    "paid": ZERO,
                },
            )
            row["amount"] += line.amount
            row["paid"] += line.amount * ratio

    fee_breakdown = []
    for row in agg.values():
        amount, ppaid = _q(row["amount"]), _q(row["paid"])
        status = (
            "paid" if ppaid >= amount and amount > ZERO else "partial" if ppaid > ZERO else "unpaid"
        )
        fee_breakdown.append(
            {
                "fee_type": row["fee_type"],
                "category": row["category"],
                "amount": str(amount),
                "paid": str(ppaid),
                "balance": str(_q(amount - ppaid)),
                "status": status,
            }
        )

    history = [
        {
            "amount": str(p.amount),
            "method": p.method,
            "paid_at": p.paid_at,
            "receipt": p.invoice.invoice_number,
            "fee_type": (p.invoice.lines.first().fee_type.name if p.invoice.lines.exists() else ""),
        }
        for p in Payment.objects.filter(invoice__student=student)
        .select_related("invoice")
        .prefetch_related("invoice__lines__fee_type")[:50]
    ]
    return {
        "total_fee": str(_q(total)),
        "paid": str(_q(paid)),
        "outstanding": str(_q(outstanding)),
        "progress_percent": round(progress, 1),
        "fee_breakdown": fee_breakdown,
        "invoices": invoice_rows,
        "payment_history": history,
    }


def collection_stats() -> dict:
    """KPI tiles for the fee-collection dashboard."""
    from apps.students.models import Student

    live = Invoice.objects.exclude(status=InvoiceStatus.CANCELLED)
    collected = live.aggregate(s=Sum("amount_paid"))["s"] or ZERO
    billed = live.aggregate(s=Sum("total"))["s"] or ZERO
    pending = billed - collected
    todays = (
        Payment.objects.filter(paid_at__date=date.today()).aggregate(s=Sum("amount"))["s"] or ZERO
    )
    total_students = Student.objects.alive().count()
    paid_students = live.filter(status=InvoiceStatus.PAID).values("student").distinct().count()
    rate = float(collected / billed * 100) if billed > ZERO else 0.0
    return {
        "total_collected": str(_q(collected)),
        "pending_dues": str(_q(pending)),
        "paid_students": paid_students,
        "total_students": total_students,
        "collection_rate_percent": round(rate, 1),
        "todays_collection": str(_q(todays)),
        "todays_receipts": Payment.objects.filter(paid_at__date=date.today()).count(),
    }


def _month_keys(months: int) -> list[str]:
    today = date.today().replace(day=1)
    keys = []
    for i in range(months - 1, -1, -1):
        m, y = today.month - i, today.year
        while m <= 0:
            m += 12
            y -= 1
        keys.append(f"{y:04d}-{m:02d}")
    return keys


def collection_dashboard(*, months: int = 12) -> dict:
    """Main fee dashboard: KPIs + monthly collected/pending + category + upcoming dues."""
    live = Invoice.objects.exclude(status=InvoiceStatus.CANCELLED)

    collected_by = {
        r["m"].strftime("%Y-%m"): r["s"]
        for r in live.annotate(m=TruncMonth("issue_date"))
        .values("m")
        .annotate(s=Sum("amount_paid"))
    }
    billed_by = {
        r["m"].strftime("%Y-%m"): r["s"]
        for r in live.annotate(m=TruncMonth("issue_date")).values("m").annotate(s=Sum("total"))
    }
    monthly = []
    for key in _month_keys(months):
        col = collected_by.get(key, ZERO)
        pend = (billed_by.get(key, ZERO)) - col
        monthly.append(
            {"month": key, "collected": _q_s(col), "pending": _q_s(pend if pend > ZERO else ZERO)}
        )

    lines = (
        InvoiceLine.objects.exclude(invoice__status=InvoiceStatus.CANCELLED)
        .values(name=F("fee_type__name"))
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    grand = sum((r["total"] for r in lines), ZERO)
    category_breakdown = [
        {
            "fee_type": r["name"],
            "amount": _q_s(r["total"]),
            "percent": round(float(r["total"] / grand * 100), 1) if grand > ZERO else 0.0,
        }
        for r in lines
    ]

    upcoming = [
        {
            "student": inv.student.full_name,
            "invoice": inv.invoice_number,
            "amount": _q_s(inv.balance),
            "due_date": inv.due_date.isoformat(),
            "days": (inv.due_date - date.today()).days,
        }
        for inv in live.filter(due_date__gte=date.today())
        .exclude(status=InvoiceStatus.PAID)
        .select_related("student")
        .order_by("due_date")[:6]
    ]

    return {
        **collection_stats(),
        "monthly": monthly,
        "category_breakdown": category_breakdown,
        "upcoming": upcoming,
    }


def _q_s(v) -> str:
    return str(_q(v))


def _bucket(days: int) -> str:
    if days <= 0:
        return "current"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


def defaulter_report() -> dict:
    """Who owes what, with aging buckets by oldest overdue due-date."""
    today = date.today()
    unpaid = (
        Invoice.objects.exclude(status=InvoiceStatus.CANCELLED)
        .annotate(bal=F("total") - F("amount_paid"))
        .filter(bal__gt=0)
        .select_related("student")
    )

    by_student: dict[int, dict] = {}
    for inv in unpaid:
        row = by_student.setdefault(
            inv.student_id,
            {
                "student": inv.student.full_name,
                "student_id": inv.student.student_id,
                "grade": inv.student.grade,
                "outstanding": ZERO,
                "oldest_due": None,
                "invoices": 0,
            },
        )
        row["outstanding"] += inv.bal
        row["invoices"] += 1
        if inv.due_date and (row["oldest_due"] is None or inv.due_date < row["oldest_due"]):
            row["oldest_due"] = inv.due_date

    aging = {"current": ZERO, "1-30": ZERO, "31-60": ZERO, "61-90": ZERO, "90+": ZERO}
    defaulters = []
    for row in by_student.values():
        oldest = row["oldest_due"]
        days = (today - oldest).days if oldest and oldest < today else 0
        bucket = _bucket(days)
        aging[bucket] += row["outstanding"]
        defaulters.append(
            {
                "student": row["student"],
                "student_id": row["student_id"],
                "grade": row["grade"],
                "outstanding": _q_s(row["outstanding"]),
                "days_overdue": days,
                "oldest_due": oldest.isoformat() if oldest else None,
                "bucket": bucket,
                "invoices": row["invoices"],
            }
        )
    defaulters.sort(key=lambda d: d["days_overdue"], reverse=True)

    total = sum((Decimal(d["outstanding"]) for d in defaulters), ZERO)
    return {
        "defaulters": defaulters,
        "aging": {k: _q_s(v) for k, v in aging.items()},
        "total_outstanding": _q_s(total),
        "count": len(defaulters),
    }


# --------------------------------------------------------------------------- #
# Predictive collections — a transparent risk score per student, from history.
# --------------------------------------------------------------------------- #
def _band(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


_ACTIONS = {
    "high": "Call guardian today; offer an instalment plan or set up UPI Autopay.",
    "medium": "Send a reminder and propose a payment plan before it ages further.",
    "low": "Monitor; the automated reminder cadence is sufficient.",
}


def _student_risk(student, invoices, bounces_by_student) -> dict | None:
    """Score one student's likelihood of not paying on time. None if nothing owed."""
    today = date.today()
    outstanding = ZERO
    overdue_count = 0
    max_days_overdue = 0
    billed = ZERO
    late_days: list[int] = []

    for inv in invoices:
        billed += inv.total
        bal = inv.total - inv.amount_paid
        if bal > ZERO:
            outstanding += bal
            if inv.due_date and inv.due_date < today:
                overdue_count += 1
                max_days_overdue = max(max_days_overdue, (today - inv.due_date).days)
        elif inv.status == InvoiceStatus.PAID and inv.due_date:
            # Historical lateness: last payment date vs due date.
            last = max((p.paid_at.date() for p in inv.payments.all()), default=None)
            if last:
                late_days.append(max(0, (last - inv.due_date).days))

    if outstanding <= ZERO:
        return None

    bounces = bounces_by_student.get(student.id, 0)
    avg_late = sum(late_days) / len(late_days) if late_days else 0
    ratio = float(outstanding / billed) if billed > ZERO else 0.0

    # Transparent weighted score (0–100).
    s_overdue = min(40.0, max_days_overdue * 0.8)
    s_count = min(15.0, overdue_count * 5.0)
    s_hist = min(20.0, avg_late * 0.5)
    s_bounce = min(15.0, bounces * 15.0)
    s_ratio = min(10.0, ratio * 10.0)
    score = int(round(min(100.0, s_overdue + s_count + s_hist + s_bounce + s_ratio)))

    reasons = []
    if max_days_overdue > 0:
        reasons.append(f"{max_days_overdue} days overdue")
    if overdue_count > 1:
        reasons.append(f"{overdue_count} overdue invoices")
    if avg_late >= 5:
        reasons.append(f"pays ~{int(avg_late)} days late on average")
    if bounces:
        reasons.append(f"{bounces} bounced cheque(s)")
    if ratio >= 0.5:
        reasons.append("large share of fees unpaid")
    if not reasons:
        reasons.append("outstanding balance, no adverse history")

    band = _band(score)
    return {
        "student": student.full_name,
        "student_id": student.student_id,
        "grade": student.grade,
        "outstanding": _q_s(outstanding),
        "risk_score": score,
        "risk_band": band,
        "days_overdue": max_days_overdue,
        "reasons": reasons,
        "recommended_action": _ACTIONS[band],
    }


def collection_risk_report(*, limit: int = 100) -> dict:
    """Rank students by predicted collection risk, with reasons + next action."""
    from django.db.models import Count

    from apps.students.models import Student

    from .models import ChequeBounce

    bounces_by_student: dict[int, int] = {
        row["invoice__student_id"]: row["n"]
        for row in ChequeBounce.objects.values("invoice__student_id").annotate(n=Count("id"))
    }

    students = (
        Student.objects.alive()
        .prefetch_related("invoices__payments")
        .filter(invoices__isnull=False)
        .distinct()
    )
    rows = []
    for student in students:
        invoices = [inv for inv in student.invoices.all() if inv.status != InvoiceStatus.CANCELLED]
        risk = _student_risk(student, invoices, bounces_by_student)
        if risk:
            rows.append(risk)

    rows.sort(key=lambda r: r["risk_score"], reverse=True)
    bands = {"high": 0, "medium": 0, "low": 0}
    for r in rows:
        bands[r["risk_band"]] += 1
    return {
        "at_risk": rows[:limit],
        "counts": bands,
        "total_at_risk": len(rows),
    }
