from django.db import models
from tenants.mixins import TenantModel


class Client(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ON_HOLD = "on_hold", "On Hold"
        CANCELLED = "cancelled", "Cancelled"

    class Department(models.TextChoices):
        SALES = "sales", "Sales"
        TECH = "tech", "Tech"
        SEO = "seo", "SEO"

    class Tag(models.TextChoices):
        VIP = "vip", "VIP"
        RETURNING = "returning", "Returning"
        URGENT = "urgent", "Urgent"
        HIGH_BUDGET = "high_budget", "High Budget"

    # Basic Info
    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=60, blank=True)
    company = models.CharField(max_length=120, blank=True)

    department = models.CharField(max_length=20, choices=Department.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    tag = models.CharField(max_length=20, choices=Tag.choices, blank=True)

    # Assignment
    assigned_to = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_clients"
    )
    converted_from = models.ForeignKey(
        "leads.Lead",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="converted_client"
    )
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_clients"
    )

    notes = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients"
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name


class SalesDetail(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="sales_detail")
    service_type = models.CharField(max_length=60)
    academic_level = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=120, blank=True)
    topic = models.CharField(max_length=200, blank=True)
    deadline = models.DateField(null=True, blank=True)
    pages = models.PositiveIntegerField(null=True, blank=True)
    word_count = models.PositiveIntegerField(null=True, blank=True)
    citation_style = models.CharField(max_length=20, blank=True)
    reference_count = models.PositiveIntegerField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)

    class Meta:
        db_table = "sales_details"


class TechDetail(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="tech_detail")
    service_type = models.CharField(max_length=60)
    platform = models.CharField(max_length=60, blank=True)
    features = models.TextField(blank=True)
    apis_needed = models.TextField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    references = models.TextField(blank=True)

    class Meta:
        db_table = "tech_details"


class SEODetail(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="seo_detail")
    website_url = models.URLField(blank=True)
    business_type = models.CharField(max_length=60, blank=True)
    keywords = models.TextField(blank=True)
    competitors = models.TextField(blank=True)
    current_ranking = models.CharField(max_length=100, blank=True)
    seo_goals = models.TextField(blank=True)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "seo_details"


class Payment(TenantModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        BANK = "bank", "Bank Transfer"
        PAYPAL = "paypal", "PayPal"
        WISE = "wise", "Wise"
        CASH = "cash", "Cash"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    method = models.CharField(max_length=20, choices=Method.choices, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]


class ClientFile(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="clients/files/")
    name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "client_files"