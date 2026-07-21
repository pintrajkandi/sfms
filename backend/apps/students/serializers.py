import re

from rest_framework import serializers

from .models import Student


def _validate_phone(value: str) -> str:
    """Optional, but if given must be exactly 10 digits (stored digits-only)."""
    if not value:
        return value
    digits = re.sub(r"\D", "", value)
    if len(digits) != 10:
        raise serializers.ValidationError("Phone number must be exactly 10 digits.")
    return digits


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    student_id = serializers.CharField(required=False)  # auto-generated if blank

    class Meta:
        model = Student
        exclude = ("search_vector",)
        read_only_fields = ("created_at", "updated_at", "deleted_at")

    def validate_phone(self, value):
        return _validate_phone(value)

    def validate_guardian_phone(self, value):
        return _validate_phone(value)
