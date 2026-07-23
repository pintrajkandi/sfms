"""Unfold dashboard data — KPI cards for the platform console index."""

from __future__ import annotations


def dashboard_callback(request, context):
    """Populate the platform dashboard with cross-school KPI cards."""
    try:
        from apps.tenants.metrics import platform_metrics

        m = platform_metrics()
    except Exception:
        m = None

    if not m:
        context["kpis"] = []
        return context

    def money(v) -> str:
        return f"₹{v}"

    context["kpis"] = [
        {
            "label": "Total schools",
            "value": m["total_schools"],
            "sub": f"{m['archived_schools']} archived",
            "tone": "indigo",
        },
        {
            "label": "Active schools",
            "value": m["active_schools"],
            "sub": f"{m['trial_schools']} on trial",
            "tone": "green",
        },
        {
            "label": "Paid schools",
            "value": m["paid_schools"],
            "sub": f"{m['trial_schools']} still on trial",
            "tone": "",
        },
        {
            "label": "Renewals ≤ 30d",
            "value": m["renewals_due_30d"],
            "sub": "upcoming",
            "tone": "amber",
        },
        {
            "label": "MRR (subscriptions)",
            "value": money(m["mrr"]),
            "sub": f"ARR {money(m['arr'])}",
            "tone": "green",
        },
    ]

    growth = m.get("growth", [])
    peak = max([g["new_schools"] for g in growth] + [1])
    context["growth"] = [{**g, "pct": int(g["new_schools"] / peak * 100)} for g in growth]

    plans = m.get("plan_mix", [])
    pmax = max([p["count"] for p in plans] + [1])
    context["plan_mix"] = [{**p, "pct": int(p["count"] / pmax * 100)} for p in plans]
    return context
