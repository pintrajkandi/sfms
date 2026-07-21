from rest_framework import serializers

from .models import (
    AcademicYear,
    Department,
    SchoolClass,
    SchoolSettings,
    Section,
    SupportTicket,
)


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "is_active")


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "subject",
            "category",
            "message",
            "contact_email",
            "status",
            "created_at",
        )
        read_only_fields = ("status", "created_at")


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ("id", "school_class", "name", "is_active")


class SchoolClassSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = SchoolClass
        fields = ("id", "name", "order", "is_active", "sections")


class SchoolSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolSettings
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and end <= start:
            raise serializers.ValidationError("end_date must be after start_date.")
        return attrs
