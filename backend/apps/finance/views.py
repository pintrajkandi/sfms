from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

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
