"""Transport: routes, vehicles and vehicle expenses (CLAUDE.md §7)."""

from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class TransportRoute(TimeStampedModel):
    """A bus route with a flat monthly transport fare per rider."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, unique=True)
    monthly_fare = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class Vehicle(TimeStampedModel):
    registration_number = models.CharField(max_length=32, unique=True)
    model = models.CharField(max_length=120, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    driver_name = models.CharField(max_length=120, blank=True)
    driver_phone = models.CharField(max_length=32, blank=True)
    route = models.ForeignKey(
        TransportRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("registration_number",)

    def __str__(self) -> str:
        return self.registration_number


class TransportExpenseCategory(models.TextChoices):
    FUEL = "fuel", "Fuel"
    DRIVER_SALARY = "driver_salary", "Driver Salary"
    MAINTENANCE = "maintenance", "Maintenance"
    INSURANCE = "insurance", "Insurance"
    OTHER = "other", "Other"


class TransportExpense(TimeStampedModel):
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses"
    )
    route = models.ForeignKey(
        TransportRoute, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses"
    )
    category = models.CharField(
        max_length=20,
        choices=TransportExpenseCategory.choices,
        default=TransportExpenseCategory.FUEL,
    )
    amount = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    spent_on = models.DateField(db_index=True)
    vendor = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=32, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-spent_on", "-created_at")

    def __str__(self) -> str:
        return f"{self.category} {self.amount} on {self.spent_on}"
