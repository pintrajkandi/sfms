from rest_framework import serializers

from .models import InventoryItem


class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        exclude = ("search_vector", "deleted_at")
        read_only_fields = ("created_at", "updated_at")
