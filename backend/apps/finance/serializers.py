from rest_framework import serializers

from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")
