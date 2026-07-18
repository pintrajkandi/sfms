"""Aggregate tenant-scoped API router (mounted at /api/v1/)."""

from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.api import (
    Auth0LoginView,
    CsrfView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ResendVerificationView,
    TenantInfoView,
    VerifyEmailView,
)
from apps.collections.views import (
    BankStatementViewSet,
    CollectionDashboardView,
    CollectionStatsView,
    DefaultersView,
    InvoiceViewSet,
    PaymentViewSet,
    RazorpayConfigView,
    RazorpayOrderView,
    RazorpayVerifyView,
)
from apps.core.audit_views import AuditLogViewSet
from apps.core.logging_api import ClientLogView
from apps.expenses.views import ExpenseViewSet
from apps.fees.views import (
    DiscountRuleViewSet,
    FeeCategoryViewSet,
    FeePlanViewSet,
    FeeTypeViewSet,
    StudentDiscountViewSet,
)
from apps.finance.views import AccountingExportView, DashboardView, LedgerEntryViewSet
from apps.inventory.views import InventoryItemViewSet
from apps.schools.views import AcademicYearViewSet, SchoolSettingsViewSet
from apps.staff.views import PayoutViewSet, TeacherViewSet
from apps.students.views import StudentViewSet

router = DefaultRouter()
router.register("students", StudentViewSet, basename="student")
router.register("fee-types", FeeTypeViewSet, basename="fee-type")
router.register("fee-categories", FeeCategoryViewSet, basename="fee-category")
router.register("fee-plans", FeePlanViewSet, basename="fee-plan")
router.register("discount-rules", DiscountRuleViewSet, basename="discount-rule")
router.register("student-discounts", StudentDiscountViewSet, basename="student-discount")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("payouts", PayoutViewSet, basename="payout")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("inventory", InventoryItemViewSet, basename="inventory")
router.register("ledger", LedgerEntryViewSet, basename="ledger")
router.register("academic-years", AcademicYearViewSet, basename="academic-year")
router.register("settings", SchoolSettingsViewSet, basename="settings")


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health, name="api-health"),
    path("client-logs/", ClientLogView.as_view(), name="client-logs"),
    # Tenant-scoped auth (served on the school subdomain).
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/tenant/", TenantInfoView.as_view(), name="auth-tenant"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/auth0/", Auth0LoginView.as_view(), name="auth-auth0"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "auth/resend-verification/",
        ResendVerificationView.as_view(),
        name="auth-resend-verification",
    ),
    path(
        "auth/password-reset/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset",
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("finance/dashboard/", DashboardView.as_view(), name="finance-dashboard"),
    path("collections/stats/", CollectionStatsView.as_view(), name="collection-stats"),
    path("collections/dashboard/", CollectionDashboardView.as_view(), name="collection-dashboard"),
    path("collections/defaulters/", DefaultersView.as_view(), name="collection-defaulters"),
    # Razorpay online payments (tenant-scoped; the webhook lives in urls_public).
    path(
        "payments/razorpay/config/",
        RazorpayConfigView.as_view(),
        name="razorpay-config",
    ),
    path("payments/razorpay/order/", RazorpayOrderView.as_view(), name="razorpay-order"),
    path("payments/razorpay/verify/", RazorpayVerifyView.as_view(), name="razorpay-verify"),
    # Parent portal (OTP-authenticated, no staff session) — filled in by apps.portal.
    path("portal/", include("apps.portal.urls")),
    *router.urls,
]
