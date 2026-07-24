"""Aggregate tenant-scoped API router (mounted at /api/v1/)."""

from django.http import JsonResponse
from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.accounts.api import (
    Auth0LoginView,
    CsrfView,
    ImpersonateView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PlatformMetricsView,
    ResendVerificationView,
    SubscriptionView,
    TeamViewSet,
    TenantInfoView,
    VerifyEmailView,
)
from apps.collections.views import (
    BankStatementViewSet,
    CollectionAssistantView,
    CollectionBreakdownView,
    CollectionDashboardView,
    CollectionRiskView,
    CollectionStatsView,
    DefaultersView,
    InvoiceViewSet,
    MandateViewSet,
    ParentLedgerView,
    PaymentViewSet,
    RazorpayConfigView,
    RazorpayOrderView,
    RazorpayVerifyView,
    SigningKeyView,
    StudentLedgerView,
)
from apps.core.audit_views import AuditLogViewSet
from apps.core.logging_api import ClientLogView
from apps.documents.views import DocumentViewSet
from apps.expenses.views import ExpenseViewSet
from apps.fees.views import (
    DiscountRuleViewSet,
    FeeCategoryViewSet,
    FeePlanViewSet,
    FeeTypeViewSet,
    StudentDiscountViewSet,
)
from apps.finance.views import (
    AccountingExportView,
    AccountViewSet,
    BalanceSheetView,
    DashboardView,
    DayBookView,
    GeneralLedgerView,
    JournalEntryViewSet,
    LedgerEntryViewSet,
    ProfitLossView,
    TrialBalanceView,
)
from apps.hostel.views import (
    HostelExpenseViewSet,
    HostelReportView,
    HostelRoomViewSet,
    HostelViewSet,
)
from apps.inventory.views import InventoryItemViewSet
from apps.notifications.views import (
    PushSubscribeView,
    PushTestView,
    PushUnsubscribeView,
    VapidKeyView,
)
from apps.privacy.views import (
    ConsentViewSet,
    DataSubjectRequestViewSet,
    StudentPrivacyView,
)
from apps.schools.views import (
    AcademicYearViewSet,
    DepartmentViewSet,
    SchoolClassViewSet,
    SchoolSettingsViewSet,
    SectionViewSet,
    SupportTicketViewSet,
)
from apps.staff.views import PayoutViewSet, TeacherViewSet
from apps.students.views import StudentViewSet
from apps.transport.views import (
    RouteProfitabilityView,
    TransportExpenseViewSet,
    TransportRouteViewSet,
    VehicleViewSet,
)

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
router.register("accounts", AccountViewSet, basename="account")
router.register("journal-entries", JournalEntryViewSet, basename="journal-entry")
router.register("academic-years", AcademicYearViewSet, basename="academic-year")
router.register("classes", SchoolClassViewSet, basename="class")
router.register("sections", SectionViewSet, basename="section")
router.register("departments", DepartmentViewSet, basename="department")
router.register("support-tickets", SupportTicketViewSet, basename="support-ticket")
router.register("transport-routes", TransportRouteViewSet, basename="transport-route")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("transport-expenses", TransportExpenseViewSet, basename="transport-expense")
router.register("hostels", HostelViewSet, basename="hostel")
router.register("hostel-rooms", HostelRoomViewSet, basename="hostel-room")
router.register("hostel-expenses", HostelExpenseViewSet, basename="hostel-expense")
router.register("documents", DocumentViewSet, basename="document")
router.register("settings", SchoolSettingsViewSet, basename="settings")
router.register("bank-statements", BankStatementViewSet, basename="bank-statement")
router.register("mandates", MandateViewSet, basename="mandate")
router.register("audit-logs", AuditLogViewSet, basename="audit-log")
router.register("consents", ConsentViewSet, basename="consent")
router.register("data-requests", DataSubjectRequestViewSet, basename="data-request")
router.register("team", TeamViewSet, basename="team")


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health, name="api-health"),
    path("client-logs/", ClientLogView.as_view(), name="client-logs"),
    # Tenant-scoped auth (served on the school subdomain).
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/tenant/", TenantInfoView.as_view(), name="auth-tenant"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/impersonate/", ImpersonateView.as_view(), name="auth-impersonate"),
    path("auth/auth0/", Auth0LoginView.as_view(), name="auth-auth0"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("subscription/", SubscriptionView.as_view(), name="subscription"),
    path("push/vapid-key/", VapidKeyView.as_view(), name="push-vapid-key"),
    path("push/subscribe/", PushSubscribeView.as_view(), name="push-subscribe"),
    path("push/unsubscribe/", PushUnsubscribeView.as_view(), name="push-unsubscribe"),
    path("push/test/", PushTestView.as_view(), name="push-test"),
    path("platform/metrics/", PlatformMetricsView.as_view(), name="platform-metrics"),
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
    path("finance/trial-balance/", TrialBalanceView.as_view(), name="finance-trial-balance"),
    path("finance/profit-loss/", ProfitLossView.as_view(), name="finance-profit-loss"),
    path("finance/balance-sheet/", BalanceSheetView.as_view(), name="finance-balance-sheet"),
    path("finance/general-ledger/", GeneralLedgerView.as_view(), name="finance-general-ledger"),
    path("finance/day-book/", DayBookView.as_view(), name="finance-day-book"),
    path(
        "transport/profitability/", RouteProfitabilityView.as_view(), name="transport-profitability"
    ),
    path("hostel/report/", HostelReportView.as_view(), name="hostel-report"),
    path(
        "finance/accounting/export/",
        AccountingExportView.as_view(),
        name="finance-accounting-export",
    ),
    path("collections/stats/", CollectionStatsView.as_view(), name="collection-stats"),
    path("collections/dashboard/", CollectionDashboardView.as_view(), name="collection-dashboard"),
    path("collections/defaulters/", DefaultersView.as_view(), name="collection-defaulters"),
    path("collections/risk/", CollectionRiskView.as_view(), name="collection-risk"),
    path("collections/breakdown/", CollectionBreakdownView.as_view(), name="collection-breakdown"),
    path(
        "collections/student-ledger/", StudentLedgerView.as_view(), name="collection-student-ledger"
    ),
    path("collections/parent-ledger/", ParentLedgerView.as_view(), name="collection-parent-ledger"),
    path("collections/signing-key/", SigningKeyView.as_view(), name="collection-signing-key"),
    path("collections/assistant/", CollectionAssistantView.as_view(), name="collection-assistant"),
    # Razorpay online payments (tenant-scoped; the webhook lives in urls_public).
    path(
        "payments/razorpay/config/",
        RazorpayConfigView.as_view(),
        name="razorpay-config",
    ),
    path("payments/razorpay/order/", RazorpayOrderView.as_view(), name="razorpay-order"),
    path("payments/razorpay/verify/", RazorpayVerifyView.as_view(), name="razorpay-verify"),
    path(
        "privacy/students/<int:pk>/",
        StudentPrivacyView.as_view(),
        name="privacy-student",
    ),
    *router.urls,
]
