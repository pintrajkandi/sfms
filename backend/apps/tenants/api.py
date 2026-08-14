"""
Public (shared-schema) onboarding API. These endpoints run OUTSIDE any tenant —
they create tenants and resolve school codes to subdomains. No auth required.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.logging import ctx, get_logger

from .models import Client
from .serializers import ResolveSchoolSerializer, SignupSerializer
from .services import TENANT_BASE_DOMAIN, provision_school, slug_available

log = get_logger("onboarding")


def _tenant_payload(client: Client) -> dict:
    domain = f"{client.slug}.{TENANT_BASE_DOMAIN}"
    # Dev runs the Vite server on :5173 over http; prod is https on the subdomain.
    is_dev = TENANT_BASE_DOMAIN in ("localhost", "127.0.0.1")
    login_url = f"http://{domain}:5173/login" if is_dev else f"https://{domain}/login"
    return {
        "school_name": client.name,
        "school_code": client.code,
        "slug": client.slug,
        "domain": domain,
        "login_url": login_url,
    }


def _schools_for_email(email: str) -> list[Client]:
    """Active schools whose (per-tenant) user table contains this email."""
    from django_tenants.utils import get_public_schema_name, schema_context

    from apps.accounts.models import User

    email = (email or "").strip()
    if not email or "@" not in email:
        return []
    public = get_public_schema_name()
    matches: list[Client] = []
    for client in (
        Client.objects.exclude(schema_name=public).filter(is_active=True).order_by("name")
    ):
        try:
            with schema_context(client.schema_name):
                if User.objects.filter(email__iexact=email, is_active=True).exists():
                    matches.append(client)
        except Exception:  # a broken tenant schema must not fail the whole lookup
            continue
    return matches


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        client = provision_school(
            name=data["school_name"],
            slug=data["slug"],
            admin_full_name=data["full_name"],
            admin_email=data["email"],
            admin_password=data["password"],
        )
        return Response(_tenant_payload(client), status=status.HTTP_201_CREATED)


class ResolveSchoolView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = ResolveSchoolSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["school_code"].strip().upper()
        try:
            client = Client.objects.get(code=code)
        except Client.DoesNotExist:
            log.warning(
                "school code not found code=%s",
                code,
                **ctx(action="resolve_school"),
            )
            return Response(
                {"detail": "No school found for that code."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(_tenant_payload(client))


class SlugAvailabilityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        slug = request.query_params.get("slug", "")
        return Response({"slug": slug, "available": slug_available(slug)})


class FindSchoolView(APIView):
    """Forgot-your-school lookup: given an email, return the matching school(s)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email or "@" not in email:
            return Response(
                {"detail": "Enter a valid email address."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        schools = _schools_for_email(email)
        log.info(
            "find-school lookup matches=%s",
            len(schools),
            **ctx(action="find_school"),
        )
        return Response({"schools": [_tenant_payload(c) for c in schools]})
