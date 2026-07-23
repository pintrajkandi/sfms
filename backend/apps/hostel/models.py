"""Hostel: buildings, rooms and hostel expenses (CLAUDE.md §6/§14)."""

from django.db import models

from apps.core.models import Currency, TimeStampedModel, money_field


class Hostel(TimeStampedModel):
    """A hostel building with a flat monthly fee per resident."""

    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, unique=True)
    monthly_fee = money_field()
    currency = models.CharField(max_length=3, choices=Currency.choices, default="INR")
    capacity = models.PositiveIntegerField(default=0)  # total beds
    warden_name = models.CharField(max_length=120, blank=True)
    warden_phone = models.CharField(max_length=32, blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class HostelRoom(TimeStampedModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("hostel", "room_number")
        constraints = [
            models.UniqueConstraint(fields=["hostel", "room_number"], name="uniq_hostel_room")
        ]

    def __str__(self) -> str:
        return f"{self.hostel.code} · Room {self.room_number}"


class HostelExpenseCategory(models.TextChoices):
    MESS = "mess", "Mess / Food"
    MAINTENANCE = "maintenance", "Maintenance"
    UTILITIES = "utilities", "Utilities"
    STAFF_SALARY = "staff_salary", "Staff Salary"
    OTHER = "other", "Other"


class HostelExpense(TimeStampedModel):
    hostel = models.ForeignKey(
        Hostel, on_delete=models.SET_NULL, null=True, blank=True, related_name="expenses"
    )
    category = models.CharField(
        max_length=20, choices=HostelExpenseCategory.choices, default=HostelExpenseCategory.MESS
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
