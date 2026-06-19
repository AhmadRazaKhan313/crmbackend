from django.contrib import admin
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "head", "is_active", "created_at")
    list_filter = ("type", "is_active")