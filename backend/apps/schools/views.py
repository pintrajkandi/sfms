from rest_framework import viewsets

from .models import AcademicYear, SchoolSettings
from .serializers import AcademicYearSerializer, SchoolSettingsSerializer


class SchoolSettingsViewSet(viewsets.ModelViewSet):
    """Tenant settings — there is effectively one row per school."""

    queryset = SchoolSettings.objects.all()
    serializer_class = SchoolSettingsSerializer


class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer
