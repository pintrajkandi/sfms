"""
Receives frontend log entries and prints them to the backend container's stdout
so all activity (frontend + backend) shows up in `docker compose logs`, not just
the browser console.
"""

from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logging import ctx, get_logger

flog = get_logger("frontend")
_LEVELS = {"info": flog.info, "warn": flog.warning, "error": flog.error}


class ClientLogView(APIView):
    """Public, unauthenticated sink for the SPA's activity log (dev visibility)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        entries = request.data.get("logs", [])
        if not isinstance(entries, list):
            entries = []
        for entry in entries[:200]:  # cap per batch
            level = str(entry.get("level", "info"))
            emit = _LEVELS.get(level, flog.info)
            emit(
                "[FE] %s | url=%s",
                str(entry.get("message", ""))[:500],
                str(entry.get("url", "-"))[:120],
                **ctx(action=str(entry.get("action", "-"))[:40]),
            )
        return Response(status=204)
