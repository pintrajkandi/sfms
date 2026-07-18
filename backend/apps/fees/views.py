from rest_framework import viewsets

from .models import FeeCategory, FeePlan, FeeType
from .serializers import FeeCategorySerializer, FeePlanSerializer, FeeTypeSerializer


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
