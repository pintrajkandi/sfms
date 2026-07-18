from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.services import ServiceError

from .models import Payout, Teacher
from .serializers import (
    PayoutSerializer,
    PayoutTransitionSerializer,
    TeacherSerializer,
)
from .services import create_payout, transition_payout


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherSerializer

    def get_queryset(self):
        return Teacher.objects.alive().prefetch_related("classes")

    def perform_destroy(self, instance):
        instance.soft_delete()


class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    queryset = Payout.objects.select_related("teacher").prefetch_related("approvals")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        payout = create_payout(
            teacher=d["teacher"],
            base_amount=d["base_amount"],
            bonus_amount=d.get("bonus_amount", 0),
            deductions=d.get("deductions", 0),
            pay_period=d["pay_period"],
            pay_type=d.get("pay_type", "salary"),
            currency=d.get("currency", "USD"),
            payment_method=d.get("payment_method", ""),
            notes=d.get("notes", ""),
            actor=request.user,
        )
        return Response(self.get_serializer(payout).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        """Advance/reject a payout through the approval workflow."""
        serializer = PayoutTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payout = transition_payout(
                payout=self.get_object(),
                to_status=serializer.validated_data["to_status"],
                actor=request.user,
                note=serializer.validated_data.get("note", ""),
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(payout).data)
