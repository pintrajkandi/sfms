from django.contrib import admin

from .models import Payout, PayoutApproval, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "department", "status", "is_active")
    search_fields = ("employee_id", "first_name", "last_name")
    list_filter = ("status", "employment_type", "is_active")


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("teacher", "pay_period", "net_amount", "status")
    list_filter = ("status", "pay_type")


admin.site.register(PayoutApproval)
