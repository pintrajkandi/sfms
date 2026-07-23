from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from apps.core.logging import ctx, get_logger

from .models import Document
from .serializers import DocumentSerializer

log = get_logger("documents")


class DocumentViewSet(viewsets.ModelViewSet):
    """Upload, list and download documents (MinIO-backed)."""

    serializer_class = DocumentSerializer
    rbac_resource = "documents"
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Document.objects.select_related("student", "uploaded_by")
        category = self.request.query_params.get("category")
        student = self.request.query_params.get("student")
        if category:
            qs = qs.filter(category=category)
        if student:
            qs = qs.filter(student_id=student)
        return qs

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        doc = serializer.save(uploaded_by=user)
        log.info(
            "document uploaded category=%s title=%s",
            doc.category,
            doc.title,
            **ctx(user=getattr(user, "id", "-"), entity=doc.id, action="upload_document"),
        )
