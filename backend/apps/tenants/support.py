"""
Read-only support-console data — runs INSIDE a tenant schema (the caller wraps
this in tenant_context). Gives support enough to debug a school ("why is
Greenfield's payout stuck?") without granting the school admin access or the
risk of a global schema switch.
"""

from __future__ import annotations


def gather_support_data() -> dict:
    from apps.accounts.models import User
    from apps.collections.models import Invoice, Payment
    from apps.staff.models import Payout
    from apps.students.models import Student

    return {
        "counts": {
            "students": Student.objects.alive().count(),
            "users": User.objects.count(),
            "invoices": Invoice.objects.count(),
            "payments": Payment.objects.count(),
            "payouts": Payout.objects.count(),
        },
        "recent_students": list(
            Student.objects.alive()
            .order_by("-created_at")[:10]
            .values("student_id", "first_name", "last_name", "grade", "status")
        ),
        "recent_invoices": list(
            Invoice.objects.order_by("-created_at")[:10].values(
                "invoice_number", "status", "total", "amount_paid", "currency"
            )
        ),
        "recent_payments": list(
            Payment.objects.order_by("-paid_at")[:10].values(
                "amount", "currency", "method", "status", "paid_at"
            )
        ),
        "payouts": list(
            Payout.objects.select_related("teacher")
            .order_by("-created_at")[:15]
            .values("id", "pay_period", "net_amount", "currency", "status", "teacher__employee_id")
        ),
        "staff": list(
            User.objects.order_by("-is_active", "email").values(
                "email", "role", "is_active", "email_verified"
            )
        ),
    }
