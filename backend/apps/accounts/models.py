"""Custom user + role. Users are tenant-scoped (each school owns its users)."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "School Admin"
    FINANCE = "finance", "Finance"
    HOD = "hod", "Head of Department"
    STAFF = "staff", "Staff"
    FRONT_DESK = "front_desk", "Front Desk"


class User(AbstractUser):
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    phone = models.CharField(max_length=32, blank=True)
    # Default True so admin/manually-provisioned users are trusted; self-service
    # signup explicitly creates the first admin as unverified (must click email link).
    email_verified = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.get_username()

    @property
    def can_review_payout_hod(self) -> bool:
        return self.role in (Role.HOD, Role.ADMIN)

    @property
    def can_review_payout_finance(self) -> bool:
        return self.role in (Role.FINANCE, Role.ADMIN)
