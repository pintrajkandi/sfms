"""
Tenant-scoped auth API. Served on the school's subdomain, so the tenant (and its
user table) is already resolved by TenantMainMiddleware. Session-based; sessions
are cache-backed with tenant-scoped keys, so one school's session never leaks to
another (apps.core.cache).
"""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.db import connection
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.email import send_mail_async
from apps.core.logging import ctx, get_logger
from apps.core.services import ServiceError

from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    StaffCreateSerializer,
    StaffUserSerializer,
    UserSerializer,
)
from .services import create_staff
from .tokens import read_email_token

log = get_logger("auth")

# Two weeks when "keep me signed in" is checked; otherwise a browser session.
REMEMBER_ME_AGE = 60 * 60 * 24 * 14


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    """Primes the csrftoken cookie for the SPA before it POSTs credentials."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        return Response({"detail": "CSRF cookie set"})


class Auth0LoginView(APIView):
    """
    Exchange an Auth0 access token for a tenant session (optional SSO).

    Validates the JWT against Auth0's JWKS (RS256, audience, issuer), resolves the
    email, and logs in the matching tenant staff user. Enabled only when
    AUTH0_DOMAIN + AUTH0_AUDIENCE are configured.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        domain, audience = settings.AUTH0_DOMAIN, settings.AUTH0_AUDIENCE
        if not domain or not audience:
            return Response(
                {"detail": "Auth0 is not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        auth_header = request.headers.get("Authorization", "")
        token = (
            auth_header[7:]
            if auth_header.startswith("Bearer ")
            else request.data.get("access_token", "")
        )
        if not token:
            return Response({"detail": "Missing access token."}, status=status.HTTP_400_BAD_REQUEST)

        issuer = f"https://{domain}/"
        try:
            import jwt
            from jwt import PyJWKClient

            signing_key = PyJWKClient(f"{issuer}.well-known/jwks.json").get_signing_key_from_jwt(
                token
            )
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=audience,
                issuer=issuer,
            )
        except Exception:  # invalid / expired / wrong audience
            log.warning("auth0 token rejected", **ctx(action="auth0_login"))
            return Response({"detail": "Invalid Auth0 token."}, status=status.HTTP_401_UNAUTHORIZED)

        email = claims.get(settings.AUTH0_EMAIL_CLAIM) or _auth0_userinfo_email(domain, token)
        if not email:
            return Response(
                {"detail": "Auth0 identity has no email; add an email claim or scope."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        User = get_user_model()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            log.warning(
                "auth0 login for unknown staff schema=%s",
                connection.schema_name,
                **ctx(action="auth0_login"),
            )
            return Response(
                {"detail": "No staff account exists for this identity at this school."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(REMEMBER_ME_AGE)
        log.info("auth0 login ok", **ctx(user=user.id, action="auth0_login"))
        return Response(UserSerializer(user).data)


def _auth0_userinfo_email(domain: str, token: str) -> str | None:
    """Fall back to Auth0 /userinfo when the access token carries no email claim."""
    import json
    import urllib.request

    req = urllib.request.Request(
        f"https://{domain}/userinfo", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 - fixed https host
            return json.loads(resp.read()).get("email")
    except Exception:
        return None


class TenantInfoView(APIView):
    """Public tenant identity for the sign-in screen (resolved from the host)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        return Response(
            {
                "name": getattr(tenant, "name", None),
                "code": getattr(tenant, "code", None),
                "slug": getattr(tenant, "slug", None),
            }
        )


class SubscriptionView(APIView):
    """The signed-in school's subscription (free plan for now)."""

    def get(self, request):
        from apps.students.models import Student
        from apps.tenants.services import subscription_status

        count = Student.objects.alive().count()
        return Response(subscription_status(request.tenant, student_count=count))


class PlatformMetricsView(APIView):
    """Cross-school SaaS metrics — platform superusers only."""

    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Platform metrics are restricted to platform administrators."},
                status=status.HTTP_403_FORBIDDEN,
            )
        from apps.tenants.metrics import platform_metrics

        return Response(platform_metrics())


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Suspended school → block sign-in (platform-console lifecycle action).
        if getattr(request.tenant, "is_active", True) is False:
            log.warning("login blocked: school suspended", **ctx(action="login"))
            return Response(
                {
                    "detail": "This school account is suspended. Contact support.",
                    "code": "school_suspended",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        code = (data.get("school_code") or "").strip().upper()
        if code and code != getattr(request.tenant, "code", None):
            log.warning(
                "login school_code mismatch code=%s",
                code,
                **ctx(action="login"),
            )
            return Response(
                {"detail": "School code does not match this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=data["email"], password=data["password"])
        if user is None:
            log.warning(
                "login failed email=%s schema=%s",
                data["email"],
                connection.schema_name,
                **ctx(action="login"),
            )
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.email_verified:
            log.warning("login blocked: unverified", **ctx(user=user.id, action="login"))
            return Response(
                {
                    "detail": "Please verify your email before signing in.",
                    "code": "email_unverified",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        request.session.set_expiry(REMEMBER_ME_AGE if data.get("keep_signed_in") else 0)
        log.info(
            "login ok",
            **ctx(user=user.id, action="login"),
        )
        return Response(UserSerializer(user).data)


class ImpersonateView(APIView):
    """
    Consume a platform-signed impersonation ticket and log in as the target user
    (support access). Ticket is SECRET_KEY-signed + schema-scoped + short-lived;
    every use is audited in the tenant schema.
    """

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        from django.core import signing

        from apps.core.audit import record_audit
        from apps.tenants.impersonation import read_ticket

        try:
            data = read_ticket(request.data.get("ticket", ""))
        except signing.SignatureExpired:
            return Response(
                {"detail": "Impersonation link expired."}, status=status.HTTP_403_FORBIDDEN
            )
        except signing.BadSignature:
            return Response(
                {"detail": "Invalid impersonation link."}, status=status.HTTP_403_FORBIDDEN
            )

        if data.get("schema") != connection.schema_name:
            return Response(
                {"detail": "Ticket is for a different school."}, status=status.HTTP_403_FORBIDDEN
            )

        User = get_user_model()
        user = User.objects.filter(pk=data.get("uid"), is_active=True).first()
        if user is None:
            return Response({"detail": "Target user not found."}, status=status.HTTP_404_NOT_FOUND)

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session.set_expiry(1800)  # 30-min support session
        request.session["impersonated_by"] = data.get("op_email")
        record_audit(
            action="impersonation.start",
            entity=user,
            summary=f"{data.get('op_email')} impersonated {user.email}",
        )
        log.warning(
            "impersonation started operator=%s target=%s",
            data.get("op_email"),
            user.id,
            **ctx(user=user.id, action="impersonate"),
        )
        return Response(UserSerializer(user).data)


class TeamViewSet(viewsets.ModelViewSet):
    """Manage a school's staff users + roles (admin-only via RBAC)."""

    serializer_class = StaffUserSerializer
    rbac_resource = "team"

    def get_queryset(self):
        User = get_user_model()
        return User.objects.all().order_by("-is_active", "first_name", "last_name")

    def create(self, request, *args, **kwargs):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        try:
            user = create_staff(
                email=d["email"],
                first_name=d["first_name"],
                last_name=d.get("last_name", ""),
                role=d["role"],
                password=d["password"],
                actor=request.user,
            )
        except ServiceError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(StaffUserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        # Don't let an admin lock themselves out.
        if instance.pk == request.user.pk and request.data.get("is_active") is False:
            raise ValidationError("You cannot deactivate your own account.")
        allowed = {
            k: request.data[k]
            for k in ("first_name", "last_name", "role", "is_active")
            if k in request.data
        }
        serializer = self.get_serializer(instance, data=allowed, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uid = request.user.id
        logout(request)
        log.info("logout ok", **ctx(user=uid, action="logout"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.schools.models import SchoolSettings

        from .permissions import permissions_for

        data = UserSerializer(request.user).data
        # Onboarding gate: the school profile is "complete" once settings has a name.
        data["settings_complete"] = SchoolSettings.objects.exclude(name="").exists()
        # Effective per-resource RBAC so the UI can hide forbidden actions.
        data["permissions"] = permissions_for(request.user.role)
        return Response(data)


class VerifyEmailView(APIView):
    """Confirm a signup email from the verification link."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        uid = read_email_token(request.data.get("token", ""))
        if uid is None:
            return Response(
                {"detail": "This verification link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        User = get_user_model()
        user = User.objects.filter(pk=uid).first()
        if user is None:
            return Response(
                {"detail": "This verification link is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        log.info("email verified", **ctx(user=user.id, action="verify_email"))
        return Response({"detail": "Email verified. You can now sign in."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        email = request.data.get("email", "")
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if user is not None and not user.email_verified:
            from .services import send_verification_email

            send_verification_email(
                user,
                school_name=getattr(request.tenant, "name", "your school"),
                slug=getattr(request.tenant, "slug", None),
            )
            log.info("verification resent", **ctx(user=user.id, action="resend_verification"))
        return Response({"detail": "If that account needs verification, a new link is on its way."})


def _reset_link(request, user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    slug = getattr(request.tenant, "slug", None)
    base = f"{slug}.{settings.TENANT_BASE_DOMAIN}" if slug else settings.TENANT_BASE_DOMAIN
    host = f"{base}:{settings.FRONTEND_PORT}" if settings.FRONTEND_PORT else base
    return f"{settings.FRONTEND_SCHEME}://{host}/reset-password?uid={uid}&token={token}"


class PasswordResetRequestView(APIView):
    """Email a reset link. Always 200 — never reveal whether an account exists."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        User = get_user_model()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None:
            link = _reset_link(request, user)
            school = getattr(request.tenant, "name", "your school")
            send_mail_async(
                to_email=user.email,
                subject=f"Reset your {school} password",
                body=(
                    f"We received a request to reset your YukiCares password for "
                    f"{school}.\n\nReset it here (link expires in a few hours):\n{link}\n\n"
                    "If you didn't request this, you can ignore this email."
                ),
                html_body=(
                    f"<p>We received a request to reset your <strong>YukiCares</strong> "
                    f"password for {school}.</p>"
                    f'<p><a href="{link}">Reset your password</a> '
                    "(link expires in a few hours).</p>"
                    "<p>If you didn't request this, you can ignore this email.</p>"
                ),
            )
            log.info("password reset requested", **ctx(user=user.id, action="password_reset"))
        else:
            log.warning(
                "password reset for unknown email schema=%s",
                connection.schema_name,
                **ctx(action="password_reset"),
            )
        return Response({"detail": "If that email exists, a reset link is on its way."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        User = get_user_model()
        try:
            uid = urlsafe_base64_decode(data["uid"]).decode()
            user = User.objects.get(pk=uid)
        except (ValueError, TypeError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, data["token"]):
            log.warning("password reset invalid token", **ctx(action="password_reset_confirm"))
            return Response(
                {"detail": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(data["new_password"], user=user)
        except serializers.ValidationError as exc:  # pragma: no cover - defensive
            return Response({"new_password": exc.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # Django's ValidationError
            return Response(
                {"new_password": list(getattr(exc, "messages", [str(exc)]))},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        log.info("password reset completed", **ctx(user=user.id, action="password_reset_confirm"))
        return Response({"detail": "Your password has been reset. You can now sign in."})
