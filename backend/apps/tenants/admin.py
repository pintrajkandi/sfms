from django.contrib import admin, messages
from django_tenants.utils import get_public_schema_name, tenant_context

from .models import Client, Domain


@admin.action(description="Resend verification email to school admin(s)")
def resend_admin_verification(modeladmin, request, queryset):
    """Master-admin action: (re)send verification to a school's unverified staff."""
    from apps.accounts.models import User
    from apps.accounts.services import send_verification_email

    public = get_public_schema_name()
    total = 0
    for client in queryset.exclude(schema_name=public):
        with tenant_context(client):
            for user in User.objects.filter(email_verified=False):
                send_verification_email(user, school_name=client.name, slug=client.slug)
                total += 1
    modeladmin.message_user(
        request,
        f"Queued {total} verification email(s) across {queryset.count()} school(s).",
        messages.SUCCESS,
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "schema_name", "code", "unverified_admins", "on_trial", "created_on")
    search_fields = ("name", "schema_name", "code")
    actions = [resend_admin_verification]

    @admin.display(description="Unverified staff")
    def unverified_admins(self, obj):
        if obj.schema_name == get_public_schema_name():
            return "—"
        from apps.accounts.models import User

        try:
            with tenant_context(obj):
                return User.objects.filter(email_verified=False).count()
        except Exception:
            return "?"


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    search_fields = ("domain",)
