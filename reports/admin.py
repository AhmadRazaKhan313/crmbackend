from django.contrib import admin
from .models import DailyReport


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "department", "status", "total_leads", "created_at")
    list_filter = ("status", "department", "date")
    search_fields = ("employee__full_name",)