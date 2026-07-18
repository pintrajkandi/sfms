from rest_framework import viewsets

from .models import DiscountRule, FeeCategory, FeePlan, FeeType, StudentDiscount
from .serializers import (
    DiscountRuleSerializer,
    FeeCategorySerializer,
    FeePlanSerializer,
    FeeTypeSerializer,
    StudentDiscountSerializer,
)


class FeeCategoryViewSet(viewsets.ModelViewSet):
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer


class FeeTypeViewSet(viewsets.ModelViewSet):
    queryset = FeeType.objects.select_related("category").all()
    serializer_class = FeeTypeSerializer


class FeePlanViewSet(viewsets.ModelViewSet):
    serializer_class = FeePlanSerializer

    def get_queryset(self):
        qs = FeePlan.objects.alive().select_related("fee_type", "academic_year")
        year = self.request.query_params.get("academic_year")
        grade = self.request.query_params.get("grade")
        if year:
            qs = qs.filter(academic_year_id=year)
        if grade:
            qs = qs.filter(grade__in=[grade, ""])
        return qs


class DiscountRuleViewSet(viewsets.ModelViewSet):
    """Scholarship / concession / sibling rules (soft-deleted, never hard)."""

    serializer_class = DiscountRuleSerializer

    def get_queryset(self):
        qs = DiscountRule.objects.alive().select_related("fee_type")
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs

    def perform_destroy(self, instance):
        instance.soft_delete()


class StudentDiscountViewSet(viewsets.ModelViewSet):
    """Awards of a rule to a student (scholarship grants, etc.)."""

    serializer_class = StudentDiscountSerializer

    def get_queryset(self):
        qs = StudentDiscount.objects.select_related("rule", "student")
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(awarded_by=user if getattr(user, "pk", None) else None)
