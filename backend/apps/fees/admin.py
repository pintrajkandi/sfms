from django.contrib import admin

from .models import FeeCategory, FeePlan, FeeType

admin.site.register(FeeCategory)
admin.site.register(FeeType)
admin.site.register(FeePlan)
