"""School inventory / assets (CLAUDE.md — Inventory)."""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.core.models import Currency, SoftDeleteModel, money_field


class ItemCategory(models.TextChoices):
    FURNITURE = "furniture", "Furniture"
    ELECTRONICS = "electronics", "Electronics"
    STATIONERY = "stationery", "Stationery"
    SPORTS = "sports", "Sports"
    LIBRARY = "library", "Library"
    LAB_EQUIPMENT = "lab_equipment", "Lab Equipment"
    CLEANING = "cleaning", "Cleaning"
    MEDICAL = "medical", "Medical"
    OTHER = "other", "Other"


class Condition(models.TextChoices):
    NEW = "new", "New"
    GOOD = "good", "Good"
    FAIR = "fair", "Fair"
    POOR = "poor", "Poor"


class InventoryItem(SoftDeleteModel):
    category = models.CharField(max_length=20, choices=ItemCategory.choices)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, unique=True)
    brand = models.CharField(max_length=120, blank=True)
    unit_of_measurement = models.CharField(max_length=32, blank=True)
    condition = models.CharField(max_length=10, choices=Condition.choices, blank=True)
    description = models.TextField(blank=True)

    # Purchase info
    unit_cost = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="USD")
    supplier_name = models.CharField(max_length=200, blank=True)
    invoice_po_number = models.CharField(max_length=64, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)

    # Stock & location
    quantity = models.PositiveIntegerField(default=0)
    min_stock_alert = models.PositiveIntegerField(default=0)
    storage_location = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=100, blank=True)
    assigned_to = models.CharField(max_length=120, blank=True)
    date_acquired = models.DateField(null=True, blank=True)

    photo = models.ImageField(upload_to="inventory/", null=True, blank=True)

    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ("name",)
        indexes = [GinIndex(fields=["search_vector"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"
