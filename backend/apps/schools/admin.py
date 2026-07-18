from django.contrib import admin

from .models import AcademicYear, SchoolSettings

admin.site.register(SchoolSettings)
admin.site.register(AcademicYear)
