"""Parent-token request helper — reads ``X-Parent-Token`` and resolves a Student."""

from __future__ import annotations

from apps.students.models import Student

from .services import read_token


def parent_from_request(request) -> Student | None:
    """Return the Student behind a valid ``X-Parent-Token`` header, else None."""
    return read_token(request.headers.get("X-Parent-Token") or "")
