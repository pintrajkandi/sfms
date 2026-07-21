"""Attaches request-scoped context (tenant + user) for structured logging."""

from __future__ import annotations

import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from apps.core.logging import ctx, get_logger

log = get_logger("http")


def _admin_prefix() -> str:
    return "/" + getattr(settings, "ADMIN_URL", "admin/").lstrip("/")


def reauth_fresh(request) -> bool:
    """True if the operator authenticated within ADMIN_REAUTH_WINDOW (sudo-style)."""
    window = getattr(settings, "ADMIN_REAUTH_WINDOW", 600)
    auth_at = request.session.get("admin_auth_at")
    return bool(auth_at and (time.time() - auth_at) <= window)


class AdminSessionTimeoutMiddleware:
    """
    Idle-timeout the platform admin console independently of the SPA session.

    After ADMIN_SESSION_TIMEOUT seconds of inactivity on an admin path the
    operator is logged out and bounced to the login page. Last-activity + the
    login timestamp (for sudo-style re-auth) are tracked in the session.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "ADMIN_SESSION_TIMEOUT", 1800)
        self.prefix = _admin_prefix()

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            request.path.startswith(self.prefix)
            and not request.path.startswith(self.prefix + "login")
            and user is not None
            and user.is_authenticated
        ):
            now = time.time()
            last = request.session.get("admin_last_seen")
            if last and now - last > self.timeout:
                log.warning(
                    "admin session idle-timeout user=%s",
                    getattr(user, "id", "-"),
                    **ctx(action="admin_timeout"),
                )
                logout(request)
                return redirect(self.prefix + "login/?next=" + request.path)
            request.session["admin_last_seen"] = now
            request.session.setdefault("admin_auth_at", now)
        return self.get_response(request)


def _client_ip(request) -> str:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class AdminIPAllowlistMiddleware:
    """
    Restrict the platform admin path to an IP allowlist (ADMIN_IP_ALLOWLIST).

    The master console is the key to every school, so we gate it at the network
    edge too. Empty allowlist = no restriction (dev). Probes are logged at `warn`.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allow = set(getattr(settings, "ADMIN_IP_ALLOWLIST", []) or [])
        self.prefix = "/" + getattr(settings, "ADMIN_URL", "admin/").lstrip("/")

    def __call__(self, request):
        if self.allow and request.path.startswith(self.prefix):
            ip = _client_ip(request)
            if ip not in self.allow:
                log.warning(
                    "admin access blocked ip=%s path=%s",
                    ip,
                    request.path,
                    **ctx(action="admin_ip_block"),
                )
                return HttpResponseForbidden("Forbidden")
        return self.get_response(request)


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log server errors at `error`, client validation issues at `warn`.
        if response.status_code >= 500:
            log.error(
                "request failed status=%s path=%s",
                response.status_code,
                request.path,
                **ctx(user=_user_id(request), action="http_request"),
            )
        elif response.status_code in (400, 403, 409, 422):
            log.warning(
                "request rejected status=%s path=%s",
                response.status_code,
                request.path,
                **ctx(user=_user_id(request), action="http_request"),
            )
        return response


def _user_id(request) -> object:
    user = getattr(request, "user", None)
    return getattr(user, "id", "-") if user and user.is_authenticated else "-"
