from datetime import date

from rest_framework import serializers

from .models import Payout, PayoutApproval, Teacher, TeacherClass


def next_employee_id() -> str:
    """Auto-generate the next employee id: TCH-<year>-<zero-padded seq>."""
    year = date.today().year
    prefix = f"TCH-{year}-"
    last = (
        Teacher.objects.filter(employee_id__startswith=prefix)
        .order_by("-employee_id")
        .values_list("employee_id", flat=True)
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            seq = Teacher.objects.filter(employee_id__startswith=prefix).count() + 1
    return f"{prefix}{seq:04d}"


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
            "employee_id": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        classes = validated_data.pop("classes", [])
        if not validated_data.get("employee_id"):
            validated_data["employee_id"] = next_employee_id()
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
            "allowances",
            "gross_amount",
            "pf_amount",
            "esi_amount",
            "tds_amount",
            "professional_tax",
            "other_deductions",
            "deductions",
            "net_amount",
            "currency",
            "days_present",
            "days_absent",
            "deduction_reason",
            "payment_method",
            "payment_reference",
            "notes",
            "status",
            "approvals",
            "created_at",
        )
        read_only_fields = (
            "gross_amount",
            "pf_amount",
            "esi_amount",
            "professional_tax",
            "net_amount",
            "status",
            "created_at",
        )


class PayoutTransitionSerializer(serializers.Serializer):
    to_status = serializers.ChoiceField(choices=Payout._meta.get_field("status").choices)
    note = serializers.CharField(required=False, allow_blank=True)


class PayrollRunSerializer(serializers.Serializer):
    """Input for a full statutory payroll run."""

    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())
    basic = serializers.DecimalField(max_digits=12, decimal_places=2)
    allowances = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    bonus = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    tds = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    other_deductions = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )
    pay_period = serializers.CharField()
    currency = serializers.CharField(required=False, default="INR")
    payment_method = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    pf_override = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    esi_override = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
    pt_override = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True
    )
