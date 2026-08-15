from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.collections.selectors import student_fee_summary
from apps.core.export import export_response

from .models import Student
from .serializers import StudentSerializer
from .services import (
    bulk_import_students,
    create_student,
    import_template_rows,
    refresh_search_vector,
)

_EXPORT_HEADERS = [
    "Student ID",
    "First Name",
    "Last Name",
    "Class",
    "Section",
    "Email",
    "Phone",
    "Guardian",
    "Guardian Phone",
    "Status",
]


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    rbac_resource = "students"

    def get_queryset(self):
        qs = Student.objects.alive()
        term = (self.request.query_params.get("search") or "").strip()
        if term:
            # Partial, typeahead-friendly search across name / id / phone. Each
            # word must match somewhere, so "Emma Johnson" matches first+last.
            for word in term.split()[:5]:
                qs = qs.filter(
                    Q(first_name__icontains=word)
                    | Q(last_name__icontains=word)
                    | Q(student_id__icontains=word)
                    | Q(phone__icontains=word)
                    | Q(guardian_phone__icontains=word)
                    | Q(guardian_name__icontains=word)
                    | Q(email__icontains=word)
                )
        # Hostel residents (students allocated to a given hostel).
        hostel = self.request.query_params.get("hostel")
        if hostel:
            qs = qs.filter(hostel_id=hostel)
        return qs

    def perform_create(self, serializer):
        from apps.tenants.limits import student_limit_for_current_tenant

        limit = student_limit_for_current_tenant()
        if limit and Student.objects.alive().count() >= limit:
            raise ValidationError(
                f"Your plan allows up to {limit} students. Upgrade to enrol more."
            )
        serializer.instance = create_student(actor=self.request.user, **serializer.validated_data)

    def perform_update(self, serializer):
        student = serializer.save()
        refresh_search_vector(student)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=["get"])
    def fees(self, request, pk=None):
        """Fee breakdown + payment progress for the student detail page."""
        return Response(student_fee_summary(self.get_object()))

    @action(detail=False, methods=["post"], url_path="import")
    def bulk_import(self, request):
        """Create students from an uploaded CSV. Returns created count + row errors."""
        upload = request.FILES.get("file")
        if not upload:
            raise ValidationError("Attach a CSV file under 'file'.")
        text = upload.read().decode("utf-8-sig", errors="replace")
        result = bulk_import_students(text, actor=request.user)
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="import-template")
    def import_template(self, request):
        headers, rows = import_template_rows()
        return export_response("csv", "student-import-template", headers, rows)

    @action(detail=False, methods=["get"])
    def export(self, request):
        fmt = request.query_params.get("fmt", "csv")
        rows = [
            [
                s.student_id,
                s.first_name,
                s.last_name,
                s.grade,
                s.section,
                s.email,
                s.phone,
                s.guardian_name,
                s.guardian_phone,
                s.status,
            ]
            for s in self.get_queryset()
        ]
        return export_response(fmt, "students", _EXPORT_HEADERS, rows)
