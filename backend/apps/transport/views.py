from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logging import ctx, get_logger

from .models import TransportExpense, TransportRoute, Vehicle
from .selectors import route_profitability
from .serializers import (
    TransportExpenseSerializer,
    TransportRouteSerializer,
    VehicleSerializer,
)

log = get_logger("transport")


class TransportRouteViewSet(viewsets.ModelViewSet):
    queryset = TransportRoute.objects.prefetch_related("vehicles", "students")
    serializer_class = TransportRouteSerializer
    rbac_resource = "transport"


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("route")
    serializer_class = VehicleSerializer
    rbac_resource = "transport"


class TransportExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = TransportExpenseSerializer
    rbac_resource = "transport"

    def get_queryset(self):
        qs = TransportExpense.objects.select_related("vehicle", "route")
        route = self.request.query_params.get("route")
        if route:
            qs = qs.filter(route_id=route)
        return qs

    def perform_create(self, serializer):
        expense = serializer.save()
        from apps.finance.ledger import _safe, post_transport_expense

        _safe(post_transport_expense, expense)
        log.info(
            "transport expense category=%s amount=%s",
            expense.category,
            expense.amount,
            **ctx(entity=expense.id, action="transport_expense"),
        )


class RouteProfitabilityView(APIView):
    rbac_resource = "transport"

    def get(self, request):
        return Response(route_profitability())
