from rest_framework import serializers

from .models import AcademicYear, SchoolSettings


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
