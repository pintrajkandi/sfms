"""Shared service-layer errors / helpers."""

from __future__ import annotations


class ServiceError(Exception):
    """Raised by service functions when a business invariant is violated."""


class InvalidTransition(ServiceError):
    """Raised when a state-machine transition is not allowed from the current state."""
