from datetime import date, timedelta

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.export import export_response

from . import accounting
from .models import LedgerEntry
from .selectors import dashboard_overview, invalidate_dashboard
from .serializers import LedgerEntrySerializer


class LedgerEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntrySerializer

    def get_queryset(self):
        qs = LedgerEntry.objects.all()
        entry_type = self.request.query_params.get("type")
        if entry_type:
            qs = qs.filter(entry_type=entry_type)
        return qs

    def perform_create(self, serializer):
        serializer.save()
        invalidate_dashboard()

    def perform_update(self, serializer):
        serializer.save()
        invalidate_dashboard()


class DashboardView(APIView):
    """Income vs expense, expense breakdown, net-savings trend (cached per tenant)."""

    def get(self, request):
        months = int(request.query_params.get("months", 6))
        return Response(dashboard_overview(months=months))


class AccountingExportView(APIView):
    """
    Export income/expense for an accounting package:
    ?target=tally|zoho|quickbooks&since=YYYY-MM-DD&until=YYYY-MM-DD.
    Tally returns XML; Zoho/QuickBooks return CSV.
    """

    def get(self, request):
        target = request.query_params.get("target", "tally").lower()
        if target not in accounting.TARGETS:
            raise ValidationError(f"target must be one of {accounting.TARGETS}.")
        until = _parse_date(request.query_params.get("until")) or date.today()
        since = _parse_date(request.query_params.get("since")) or (until - timedelta(days=90))
        if since > until:
            raise ValidationError("since must be on or before until.")

        kind, filename, payload = accounting.build_export(target, since, until)
        if kind == "xml":
            resp = HttpResponse(payload, content_type="application/xml")
            resp["Content-Disposition"] = f'attachment; filename="{filename}.xml"'
            return resp
        headers, rows = payload
        return export_response("csv", filename, headers, rows)


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"Invalid date: {value}") from exc
