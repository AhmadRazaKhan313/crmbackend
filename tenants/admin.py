from django.contrib import admin
from .models import Tenant, TenantFeature


class TenantFeatureInline(admin.StackedInline):
    model = TenantFeature
    can_delete = False


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "email", "plan", "status", "created_at")
    list_filter = ("plan", "status")
    search_fields = ("name", "email", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TenantFeatureInline]