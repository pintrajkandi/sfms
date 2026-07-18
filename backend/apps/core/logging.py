"""
Application logging helpers — enforces the info/warn/error contract (CLAUDE.md §9).

Usage:
    from apps.core.logging import get_logger
    log = get_logger(__name__)
    log.info("payment recorded", extra=ctx(entity=payment.id, action="record_payment"))

Never pass secrets or raw PII in the message or context — ids and amounts only.
"""

from __future__ import annotations

import logging

from apps.core.cache import current_schema


def get_logger(name: str) -> logging.Logger:
    # Namespacing under "sfms" routes through the app logger in config/logging.py.
    return logging.getLogger(f"sfms.{name}")


def ctx(*, user: object = "-", entity: object = "-", action: str = "-") -> dict:
    """Build the structured `extra` dict; tenant is filled in automatically."""
    return {
        "extra": {
            "tenant": current_schema(),
            "user": user,
            "entity": entity,
            "action": action,
        }
    }
