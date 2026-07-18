from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "first_name", "last_name", "grade", "is_active")
    search_fields = ("student_id", "first_name", "last_name", "guardian_name")
    list_filter = ("grade", "department", "is_active")
