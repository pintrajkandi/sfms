"""Public-schema URL configuration (provisioning / platform admin)."""

from django.conf import settings
from django.http import JsonResponse
from django.urls import path

from apps.collections.views import RazorpayWebhookView
from apps.core.logging_api import ClientLogView
from apps.tenants.admin_site import platform_admin
from apps.tenants.api import ResolveSchoolView, SignupView, SlugAvailabilityView


def health(_request):
    return JsonResponse({"status": "ok", "schema": "public"})


# Master console path is settings-driven (move it off the well-known /admin/).
_ADMIN_URL = getattr(settings, "ADMIN_URL", "admin/")

urlpatterns = [
    path(_ADMIN_URL, platform_admin.urls),
    path("health/", health, name="health"),
    # Frontend log sink (apex host — signup/login pages).
    path("api/v1/client-logs/", ClientLogView.as_view(), name="public-client-logs"),
    # Onboarding (create a school) + school-code resolution — no tenant, no auth.
    path("api/v1/onboarding/signup/", SignupView.as_view(), name="onboarding-signup"),
    path("api/v1/onboarding/resolve/", ResolveSchoolView.as_view(), name="onboarding-resolve"),
    path(
        "api/v1/onboarding/slug-available/",
        SlugAvailabilityView.as_view(),
        name="onboarding-slug",
    ),
    # Razorpay webhook — single URL, no tenant subdomain; reconciles into the
    # tenant schema carried in the order notes.
    path(
        "webhooks/razorpay/",
        RazorpayWebhookView.as_view(),
        name="razorpay-webhook",
    ),
]
