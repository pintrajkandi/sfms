"""
Tenant-scoped URL configuration (resolved inside a school's schema).

NOTE: Django admin is intentionally NOT mounted here. Only the platform (public
schema) exposes /admin/ — see config/urls_public.py. School staff use the app UI
and the tenant auth API; they never get the Django admin.
"""

from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("apps.core.api_urls")),
]
