from django.contrib import admin

from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "condition", "unit_cost", "is_active")
    list_filter = ("category", "condition", "is_active")
    search_fields = ("name", "sku", "supplier_name")
