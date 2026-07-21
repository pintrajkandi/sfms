"""Student enrollment records (CLAUDE.md — Students)."""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.core.models import SoftDeleteModel


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"


class EnrollmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    GRADUATED = "graduated", "Graduated"
    TRANSFERRED = "transferred", "Transferred"
    SUSPENDED = "suspended", "Suspended"


class Student(SoftDeleteModel):
    # Human-facing id (e.g. STU-2024-001); unique within the tenant schema.
    student_id = models.CharField(max_length=32, unique=True)

    # Personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    photo = models.ImageField(upload_to="students/", null=True, blank=True)

    # Contact
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    home_address = models.TextField(blank=True)

    # Guardian
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)
    guardian_phone = models.CharField(max_length=32, blank=True)
    guardian_email = models.EmailField(blank=True)

    # Academic. `grade` stores the managed class name; `section` the section name.
    department = models.CharField(max_length=100, blank=True)
    grade = models.CharField(max_length=50, blank=True)  # class (managed via SchoolClass)
    section = models.CharField(max_length=50, blank=True)  # section (managed via Section)
    enrollment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=EnrollmentStatus.choices, default=EnrollmentStatus.ACTIVE
    )
    previous_school = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    academic_year = models.ForeignKey(
        "schools.AcademicYear",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="students",
    )

    search_vector = SearchVectorField(null=True, editable=False)

    class Meta:
        ordering = ("first_name", "last_name")
        indexes = [GinIndex(fields=["search_vector"])]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
