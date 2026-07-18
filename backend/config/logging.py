"""
Logging configuration — THREE LEVELS ONLY: info / warn / error (see CLAUDE.md §9).

Python's native levels are DEBUG/INFO/WARNING/ERROR/CRITICAL. We:
  * emit nothing below INFO in normal operation, and
  * normalise the level name in the formatter so output reads
    `[info] [warn] [error]` (WARNING -> warn, CRITICAL -> error).

Every record carries structured context: tenant, user, entity, action —
injected by apps.core.middleware + apps.core.logging helpers.
"""

from __future__ import annotations

import logging

_LEVEL_NAME_MAP = {
    "DEBUG": "info",  # collapsed upward — we don't use debug as an app level
    "INFO": "info",
    "WARNING": "warn",
    "ERROR": "error",
    "CRITICAL": "error",  # collapsed downward — fatal failures log as error
}


class ThreeLevelFilter(logging.Filter):
    """Attach normalised `levelname` + default context fields to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.levelname = _LEVEL_NAME_MAP.get(record.levelname, "info")
        for field in ("tenant", "user", "entity", "action"):
            if not hasattr(record, field):
                setattr(record, field, "-")
        return True


def build_logging_config(level: str = "INFO") -> dict:
    level = level.upper()
    if level not in ("INFO", "WARNING", "ERROR"):
        level = "INFO"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "three_level": {"()": "config.logging.ThreeLevelFilter"},
        },
        "formatters": {
            "structured": {
                "format": (
                    "[%(levelname)s] %(asctime)s %(name)s "
                    "tenant=%(tenant)s user=%(user)s entity=%(entity)s "
                    "action=%(action)s :: %(message)s"
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "filters": ["three_level"],
                "formatter": "structured",
                "level": level,
            },
        },
        "root": {"handlers": ["console"], "level": level},
        "loggers": {
            # Django's own noise stays at warn+ so it doesn't drown the audit trail.
            "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
            # Application logger — the business audit trail.
            "sfms": {"handlers": ["console"], "level": level, "propagate": False},
            "celery": {"handlers": ["console"], "level": level, "propagate": False},
        },
    }
