from rest_framework import serializers

from .models import ConsentRecord, DataSubjectRequest


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = (
            "id",
            "student",
            "purpose",
            "granted",
            "source",
            "note",
            "recorded_by",
            "updated_at",
        )
        read_only_fields = ("recorded_by", "updated_at")


class DataSubjectRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSubjectRequest
        fields = (
            "id",
            "student",
            "subject_label",
            "kind",
            "status",
            "summary",
            "requested_by",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields
