from rest_framework import serializers

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_superuser",
        )

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username


class StaffUserSerializer(serializers.ModelSerializer):
    """Read shape for the Team & Roles screen."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_active",
            "email_verified",
            "last_login",
            "date_joined",
        )
        read_only_fields = ("email_verified", "last_login", "date_joined")

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.email


class StaffCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    role = serializers.ChoiceField(choices=Role.choices)
    password = serializers.CharField(min_length=8, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    # Optional — the tenant is authoritative from the request host; when supplied
    # we verify it matches (extra guard + parity with the sign-in screen).
    school_code = serializers.CharField(required=False, allow_blank=True)
    keep_signed_in = serializers.BooleanField(required=False, default=False)
