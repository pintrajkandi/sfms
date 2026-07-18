from rest_framework import serializers

from .models import Student


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    student_id = serializers.CharField(required=False)  # auto-generated if blank

    class Meta:
        model = Student
        exclude = ("search_vector",)
        read_only_fields = ("created_at", "updated_at", "deleted_at")
