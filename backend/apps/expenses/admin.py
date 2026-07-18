from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "amount", "currency", "expense_date", "reimbursable")
    list_filter = ("category", "reimbursable")
    search_fields = ("title", "vendor")
