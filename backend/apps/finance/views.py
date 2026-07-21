from datetime import date, timedelta

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.export import export_response

from . import accounting, statements
from .models import Account, JournalEntry, LedgerEntry
from .selectors import dashboard_overview, invalidate_dashboard
from .serializers import (
    AccountSerializer,
    JournalEntrySerializer,
    LedgerEntrySerializer,
)


class LedgerEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LedgerEntrySerializer
    rbac_resource = "ledger"

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


class AccountViewSet(viewsets.ModelViewSet):
    """Chart of accounts. System accounts cannot be deleted."""

    serializer_class = AccountSerializer
    rbac_resource = "accounts"

    def get_queryset(self):
        qs = Account.objects.all()
        acc_type = self.request.query_params.get("type")
        if acc_type:
            qs = qs.filter(type=acc_type)
        return qs

    def perform_destroy(self, instance):
        if instance.is_system:
            raise ValidationError("System accounts cannot be deleted; deactivate instead.")
        instance.delete()


class JournalEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable journal. Filter with ?source_type=payment or ?account=<code>."""

    serializer_class = JournalEntrySerializer
    rbac_resource = "journal"

    def get_queryset(self):
        qs = JournalEntry.objects.prefetch_related("lines__account")
        source_type = self.request.query_params.get("source_type")
        account = self.request.query_params.get("account")
        if source_type:
            qs = qs.filter(source_type=source_type)
        if account:
            qs = qs.filter(lines__account__code=account).distinct()
        return qs


class DashboardView(APIView):
    """Income vs expense, expense breakdown, net-savings trend (cached per tenant)."""

    def get(self, request):
        months = int(request.query_params.get("months", 6))
        return Response(dashboard_overview(months=months))


class TrialBalanceView(APIView):
    def get(self, request):
        as_of = _parse_date(request.query_params.get("as_of"))
        return Response(statements.trial_balance(as_of=as_of))


class ProfitLossView(APIView):
    def get(self, request):
        since = _parse_date(request.query_params.get("since"))
        until = _parse_date(request.query_params.get("until"))
        return Response(statements.profit_and_loss(since=since, until=until))


class BalanceSheetView(APIView):
    def get(self, request):
        as_of = _parse_date(request.query_params.get("as_of"))
        return Response(statements.balance_sheet(as_of=as_of))


class GeneralLedgerView(APIView):
    def get(self, request):
        code = request.query_params.get("account")
        if not code:
            raise ValidationError("An 'account' code is required.")
        since = _parse_date(request.query_params.get("since"))
        until = _parse_date(request.query_params.get("until"))
        return Response(statements.general_ledger(account_code=code, since=since, until=until))


class DayBookView(APIView):
    def get(self, request):
        since = _parse_date(request.query_params.get("since"))
        until = _parse_date(request.query_params.get("until"))
        return Response(statements.day_book(since=since, until=until))


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
