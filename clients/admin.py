from django.contrib import admin
from .models import Client, SalesDetail, TechDetail, SEODetail, Payment, ClientFile


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "department", "status", "tag", "assigned_to", "created_at")
    list_filter = ("status", "department", "tag")
    search_fields = ("full_name", "email", "phone")


@admin.register(SalesDetail)
class SalesDetailAdmin(admin.ModelAdmin):
    list_display = ("client", "service_type", "academic_level", "subject", "deadline")
    search_fields = ("client__full_name", "subject")


@admin.register(TechDetail)
class TechDetailAdmin(admin.ModelAdmin):
    list_display = ("client", "service_type", "platform", "deadline", "budget")
    search_fields = ("client__full_name", "service_type")


@admin.register(SEODetail)
class SEODetailAdmin(admin.ModelAdmin):
    list_display = ("client", "website_url", "business_type", "monthly_budget")
    search_fields = ("client__full_name", "website_url")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("client", "amount", "paid_amount", "status", "method", "created_at")
    list_filter = ("status", "method")


@admin.register(ClientFile)
class ClientFileAdmin(admin.ModelAdmin):
    list_display = ("client", "name", "uploaded_by", "uploaded_at")
    search_fields = ("client__full_name", "name")