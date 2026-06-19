from django.contrib import admin
from .models import Lead, LeadActivity


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "status", "source", "assigned_to", "created_at")
    list_filter = ("status", "department", "source")
    search_fields = ("full_name", "email", "phone")


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ("lead", "activity_type", "created_by", "created_at")