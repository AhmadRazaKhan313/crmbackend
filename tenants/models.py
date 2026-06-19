from django.db import models


class Tenant(models.Model):
    class Plan(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        TRIAL = "trial", "Trial"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to="tenants/logos/", blank=True, null=True)

    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)

    trial_ends_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class TenantFeature(models.Model):
    """Per-tenant feature flags."""
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="features")

    # ── Core CRM Modules ──────────────────────────────────────
    leads_module    = models.BooleanField(default=True)
    clients_module  = models.BooleanField(default=True)
    tasks_module    = models.BooleanField(default=True)
    reports_module  = models.BooleanField(default=True)
    departments_module = models.BooleanField(default=True)

    # ── Add-on Modules ────────────────────────────────────────
    analytics       = models.BooleanField(default=True)
    hrms            = models.BooleanField(default=False)
    ai_assistant    = models.BooleanField(default=False)

    # ── Platform Features ─────────────────────────────────────
    multi_department  = models.BooleanField(default=True)
    custom_branding   = models.BooleanField(default=False)
    api_access        = models.BooleanField(default=False)

    class Meta:
        db_table = "tenant_features"

    def __str__(self):
        return f"{self.tenant.name} — features"
