from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .services import normalize_slug, slug_available


class SignupSerializer(serializers.Serializer):
    """Create your school's account (public onboarding)."""

    school_name = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=63)  # the "web address" label
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    agree_terms = serializers.BooleanField()

    def validate_slug(self, value):
        slug = normalize_slug(value)
        if not slug_available(slug):
            raise serializers.ValidationError("That web address is taken or invalid.")
        return slug

    def validate_agree_terms(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms of service.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs


class ResolveSchoolSerializer(serializers.Serializer):
    """Look up a school by its code so the sign-in page can route to the tenant."""

    school_code = serializers.CharField(max_length=16)
