"""Attaches request-scoped context (tenant + user) for structured logging."""

from __future__ import annotations

from apps.core.logging import ctx, get_logger

log = get_logger("http")


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
