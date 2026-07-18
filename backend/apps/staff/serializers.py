from rest_framework import serializers

from .models import Payout, PayoutApproval, Teacher, TeacherClass


class TeacherClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherClass
        fields = ("id", "class_name", "role_in_class", "academic_year")


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    classes = TeacherClassSerializer(many=True, required=False)

    class Meta:
        model = Teacher
        exclude = ("deleted_at",)
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {
            "account_number": {"write_only": True},
            "first_name": {"required": True, "allow_blank": False},
            "employee_id": {"required": True},
        }

    def create(self, validated_data):
        classes = validated_data.pop("classes", [])
        teacher = Teacher.objects.create(**validated_data)
        for row in classes:
            TeacherClass.objects.create(teacher=teacher, **row)
        return teacher

    def update(self, instance, validated_data):
        classes = validated_data.pop("classes", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if classes is not None:
            instance.classes.all().delete()
            for row in classes:
                TeacherClass.objects.create(teacher=instance, **row)
        return instance


class PayoutApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayoutApproval
        fields = ("from_status", "to_status", "actor", "note", "created_at")


class PayoutSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    approvals = PayoutApprovalSerializer(many=True, read_only=True)

    class Meta:
        model = Payout
        fields = (
            "id",
            "teacher",
            "teacher_name",
            "pay_type",
            "pay_period",
            "base_amount",
            "bonus_amount",
            "deductions",
            "net_amount",
            "currency",
            "payment_method",
            "notes",
            "status",
            "approvals",
            "created_at",
        )
        read_only_fields = ("net_amount", "status", "created_at")


class PayoutTransitionSerializer(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=Payout._meta.get_field("status").choices)
    note = serializers.CharField(required=False, allow_blank=True)
