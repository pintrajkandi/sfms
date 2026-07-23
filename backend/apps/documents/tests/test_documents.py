"""Document upload + category/student filtering."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.documents.models import Document
from apps.documents.serializers import DocumentSerializer

pytestmark = [pytest.mark.django_db]

# Keep uploads off MinIO during tests.
MEM_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=MEM_STORAGE)
def test_document_upload_and_filter(tenant_ctx):
    f = SimpleUploadedFile("id-card.pdf", b"%PDF-1.4 test", content_type="application/pdf")
    serializer = DocumentSerializer(data={"title": "ID Card", "category": "student", "file": f})
    assert serializer.is_valid(), serializer.errors
    doc = serializer.save()

    assert doc.category == "student"
    assert Document.objects.filter(category="student").count() == 1
    assert Document.objects.filter(category="invoice").count() == 0


def test_document_requires_title_and_file(tenant_ctx):
    serializer = DocumentSerializer(data={"category": "receipt"})
    assert not serializer.is_valid()
    assert "title" in serializer.errors
    assert "file" in serializer.errors
