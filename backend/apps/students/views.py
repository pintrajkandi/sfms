from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.collections.selectors import student_fee_summary
from apps.core.search import full_text_search

from .models import Student
from .serializers import StudentSerializer
from .services import create_student, refresh_search_vector


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer

    def get_queryset(self):
        qs = Student.objects.alive()
        term = self.request.query_params.get("search")
        if term:
            qs = full_text_search(qs, term)
        return qs

    def perform_create(self, serializer):
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
