"""Parent-portal URL patterns (mounted at /api/v1/portal/)."""

from django.urls import path

from .views import (
    PortalFeesView,
    PortalInvoicesView,
    PortalPayOrderView,
    PortalPayVerifyView,
    RequestOtpView,
    VerifyOtpView,
)

urlpatterns = [
    path("request-otp/", RequestOtpView.as_view(), name="portal-request-otp"),
    path("verify-otp/", VerifyOtpView.as_view(), name="portal-verify-otp"),
    path("fees/", PortalFeesView.as_view(), name="portal-fees"),
    path("invoices/", PortalInvoicesView.as_view(), name="portal-invoices"),
    path("pay/order/", PortalPayOrderView.as_view(), name="portal-pay-order"),
    path("pay/verify/", PortalPayVerifyView.as_view(), name="portal-pay-verify"),
]
