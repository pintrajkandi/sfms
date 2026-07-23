from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logging import ctx, get_logger

from .models import Hostel, HostelExpense, HostelRoom
from .selectors import hostel_report
from .serializers import HostelExpenseSerializer, HostelRoomSerializer, HostelSerializer

log = get_logger("hostel")


class HostelViewSet(viewsets.ModelViewSet):
    queryset = Hostel.objects.prefetch_related("rooms", "residents")
    serializer_class = HostelSerializer
    rbac_resource = "hostel"


class HostelRoomViewSet(viewsets.ModelViewSet):
    serializer_class = HostelRoomSerializer
    rbac_resource = "hostel"

    def get_queryset(self):
        qs = HostelRoom.objects.select_related("hostel")
        hostel = self.request.query_params.get("hostel")
        if hostel:
            qs = qs.filter(hostel_id=hostel)
        return qs


class HostelExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = HostelExpenseSerializer
    rbac_resource = "hostel"

    def get_queryset(self):
        qs = HostelExpense.objects.select_related("hostel")
        hostel = self.request.query_params.get("hostel")
        if hostel:
            qs = qs.filter(hostel_id=hostel)
        return qs

    def perform_create(self, serializer):
        expense = serializer.save()
        from apps.finance.ledger import _safe, post_hostel_expense

        _safe(post_hostel_expense, expense)
        log.info(
            "hostel expense category=%s amount=%s",
            expense.category,
            expense.amount,
            **ctx(entity=expense.id, action="hostel_expense"),
        )


class HostelReportView(APIView):
    rbac_resource = "hostel"

    def get(self, request):
        return Response(hostel_report())
