"""
AI collections assistant (CLAUDE.md roadmap).

Answers natural-language questions about the tenant's fee collections, grounded in
the predictive risk report + collection KPIs. Env-gated on ANTHROPIC_API_KEY: with
a key it calls Claude (official anthropic SDK); without one it returns a
deterministic rule-based summary so the endpoint is always useful in dev. The
model only ever sees aggregated, PII-safe figures — never raw personal data.
"""

from __future__ import annotations

import json

from django.conf import settings

from apps.core.logging import ctx, get_logger

from .selectors import collection_risk_report, collection_stats, defaulter_report

log = get_logger("collections.assistant")

_SYSTEM = (
    "You are a fee-collections assistant for a school finance team. Answer the "
    "user's question using ONLY the JSON data provided (KPIs, aging buckets, and "
    "per-student risk scores). Be concise and specific: cite numbers, name the "
    "highest-risk students, and recommend concrete next actions. If the data does "
    "not contain the answer, say so."
)


def assistant_enabled() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def _context(limit: int = 20) -> dict:
    """Aggregated, PII-safe snapshot handed to the model as grounding."""
    risk = collection_risk_report(limit=limit)
    defaulters = defaulter_report()
    return {
        "kpis": collection_stats(),
        "aging": defaulters["aging"],
        "total_outstanding": defaulters["total_outstanding"],
        "risk_counts": risk["counts"],
        "at_risk": risk["at_risk"],
    }


def _fallback_answer(question: str, data: dict) -> str:
    """Deterministic summary when no Claude key is configured (dev)."""
    counts = data["risk_counts"]
    top = data["at_risk"][:3]
    lines = [
        f"Outstanding: {data['total_outstanding']} across "
        f"{data['kpis']['total_students']} students "
        f"(collection rate {data['kpis']['collection_rate_percent']}%).",
        f"Risk: {counts['high']} high, {counts['medium']} medium, {counts['low']} low.",
    ]
    if top:
        lines.append("Highest-risk students:")
        for r in top:
            lines.append(
                f"  • {r['student']} ({r['grade']}) — score {r['risk_score']} "
                f"[{r['risk_band']}], owes {r['outstanding']}; {r['recommended_action']}"
            )
    lines.append("(AI assistant not configured — set ANTHROPIC_API_KEY for tailored answers.)")
    return "\n".join(lines)


def ask(question: str, *, limit: int = 20) -> dict:
    """Answer a collections question. Returns {answer, source, at_risk_count}."""
    data = _context(limit=limit)

    if not assistant_enabled():
        return {
            "answer": _fallback_answer(question, data),
            "source": "rule-based",
            "at_risk_count": data["risk_counts"]["high"] + data["risk_counts"]["medium"],
        }

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1024,
            system=_SYSTEM,
            thinking={"type": "adaptive"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\n"
                        f"Collection data (JSON):\n{json.dumps(data, indent=2)}"
                    ),
                }
            ],
        )
        answer = next((b.text for b in message.content if b.type == "text"), "").strip()
        log.info(
            "assistant answered chars=%s model=%s",
            len(answer),
            settings.ANTHROPIC_MODEL,
            **ctx(action="assistant_ask"),
        )
        return {"answer": answer, "source": "claude", "at_risk_count": len(data["at_risk"])}
    except Exception as exc:
        # Never fail the request on an assistant hiccup — fall back to the summary.
        log.warning(
            "assistant call failed, using fallback error=%s",
            exc,
            **ctx(action="assistant_ask"),
        )
        return {
            "answer": _fallback_answer(question, data),
            "source": "rule-based-fallback",
            "at_risk_count": data["risk_counts"]["high"] + data["risk_counts"]["medium"],
        }
