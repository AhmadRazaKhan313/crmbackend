from django.db import models
from tenants.mixins import TenantModel


class Invoice(TenantModel):
    class Status(models.TextChoices):
        DRAFT     = "draft",     "Draft"
        SENT      = "sent",      "Sent"
        PAID      = "paid",      "Paid"
        OVERDUE   = "overdue",   "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    invoice_no   = models.CharField(max_length=20, blank=True)
    client       = models.ForeignKey(
        "clients.Client", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="invoices"
    )
    client_name  = models.CharField(max_length=120)
    client_email = models.EmailField(blank=True)
    issued_by    = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL,
        null=True, related_name="issued_invoices"
    )
    amount       = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency     = models.CharField(max_length=10, default="USD")
    items        = models.JSONField(default=list)
    status       = models.CharField(max_length=15, choices=Status.choices, default=Status.DRAFT)
    due_date     = models.DateField(null=True, blank=True)
    paid_at      = models.DateTimeField(null=True, blank=True)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-created_at"]

    @property
    def balance_due(self):
        return float(self.amount) - float(self.paid_amount)

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            last = Invoice.objects.filter(tenant=self.tenant).exclude(invoice_no="").order_by("-created_at").first()
            if last and last.invoice_no.startswith("INV-"):
                try:
                    num = int(last.invoice_no.split("-")[1]) + 1
                except (IndexError, ValueError):
                    num = 1
            else:
                num = 1
            self.invoice_no = f"INV-{str(num).zfill(4)}"
        super().save(*args, **kwargs)


class Expense(TenantModel):
    class Category(models.TextChoices):
        SALARY    = "salary",    "Salary"
        OFFICE    = "office",    "Office"
        MARKETING = "marketing", "Marketing"
        TOOLS     = "tools",     "Tools & Software"
        TRAVEL    = "travel",    "Travel"
        OTHER     = "other",     "Other"

    title      = models.CharField(max_length=200)
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    currency   = models.CharField(max_length=10, default="USD")
    category   = models.CharField(max_length=20, choices=Category.choices)
    department = models.CharField(max_length=20, blank=True)
    date       = models.DateField()
    paid_by    = models.ForeignKey(
        "authentication.User", on_delete=models.SET_NULL,
        null=True, related_name="expenses"
    )
    notes      = models.TextField(blank=True)
    receipt    = models.FileField(upload_to="expenses/receipts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expenses"
        ordering = ["-date"]
