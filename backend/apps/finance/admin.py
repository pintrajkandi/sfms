from django.contrib import admin

from .models import LedgerEntry


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("entry_type", "category", "amount", "currency", "occurred_on")
    list_filter = ("entry_type",)
    search_fields = ("category", "description")
