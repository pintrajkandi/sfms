from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "full_name", "role")

    def get_full_name(self, obj) -> str:
        return obj.get_full_name() or obj.username


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
