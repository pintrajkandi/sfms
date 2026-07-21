"""Data-privacy API — export, erasure, consent, and the request log."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.students.models import Student

from . import services
from .models import ConsentRecord, DataSubjectRequest
from .serializers import ConsentRecordSerializer, DataSubjectRequestSerializer


def _student_or_404(pk) -> Student:
    student = Student.objects.filter(pk=pk).first()
    if student is None:
        raise NotFound("Student not found.")
    return student


class StudentPrivacyView(APIView):
    """Per-student data-subject actions (admin-only via RBAC)."""

    rbac_resource = "privacy"

    def get(self, request, pk=None):
        """Right of access: export everything held on the student."""
        student = _student_or_404(pk)
        data = services.export_student_data(student)
        services.log_access_request(student, actor=request.user)
        return Response(data)

    def delete(self, request, pk=None):
        """Right to erasure: anonymize PII, keep financial records."""
        student = _student_or_404(pk)
        req = services.erase_student_data(
            student, reason=request.data.get("reason", ""), actor=request.user
        )
        return Response(DataSubjectRequestSerializer(req).data, status=status.HTTP_200_OK)


class ConsentViewSet(viewsets.ModelViewSet):
    """Consent ledger. Creating/updating upserts per (student, purpose)."""

    serializer_class = ConsentRecordSerializer
    rbac_resource = "consents"

    def get_queryset(self):
        qs = ConsentRecord.objects.select_related("student")
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        consent = services.record_consent(
            student=d["student"],
            purpose=d["purpose"],
            granted=d["granted"],
            source=d.get("source", "staff"),
            note=d.get("note", ""),
            actor=request.user,
        )
        return Response(self.get_serializer(consent).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def retention_sweep(self, request):
        """Erase PII of students who left longer ago than the retention window."""
        days = int(request.data.get("anonymize_after_days", 2555))  # ~7 years default
        return Response(services.run_retention(anonymize_after_days=days, actor=request.user))


class DataSubjectRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """Immutable log of data-subject requests (access/erasure/rectification)."""

    serializer_class = DataSubjectRequestSerializer
    rbac_resource = "data-requests"

    def get_queryset(self):
        qs = DataSubjectRequest.objects.all()
        kind = self.request.query_params.get("kind")
        if kind:
            qs = qs.filter(kind=kind)
        return qs
