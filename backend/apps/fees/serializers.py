from rest_framework import serializers

from .models import DiscountRule, FeeCategory, FeePlan, FeeType, StudentDiscount


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


class DiscountRuleSerializer(serializers.ModelSerializer):
    fee_type_name = serializers.CharField(source="fee_type.name", read_only=True)

    class Meta:
        model = DiscountRule
        exclude = ("is_active", "deleted_at")
        read_only_fields = ("created_at", "updated_at")


class StudentDiscountSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)
    rule_kind = serializers.CharField(source="rule.kind", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = StudentDiscount
        fields = (
            "id",
            "student",
            "student_name",
            "rule",
            "rule_name",
            "rule_kind",
            "override_value",
            "is_active",
            "valid_from",
            "valid_to",
            "note",
            "awarded_by",
            "created_at",
        )
        read_only_fields = ("awarded_by", "created_at")
