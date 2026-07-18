from rest_framework import serializers

from .models import FeeCategory, FeePlan, FeeType


class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class FeeTypeSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = FeeType
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")


class FeePlanSerializer(serializers.ModelSerializer):
    fee_type_name = serializers.CharField(source="fee_type.name", read_only=True)

    class Meta:
        model = FeePlan
        exclude = ("is_active", "deleted_at")
        read_only_fields = ("created_at", "updated_at")
