from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True, default="")
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True, default=""
    )

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "category",
            "file",
            "student",
            "student_name",
            "notes",
            "uploaded_by",
            "uploaded_by_name",
            "created_at",
        )
        read_only_fields = ("uploaded_by", "created_at")
