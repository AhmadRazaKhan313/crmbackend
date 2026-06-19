from django.db import models
from tenants.mixins import TenantModel


class Department(TenantModel):
    class Type(models.TextChoices):
        SALES = "sales", "Sales"
        TECH = "tech", "Tech"
        SEO = "seo", "SEO"

    name = models.CharField(max_length=60)
    type = models.CharField(max_length=20, choices=Type.choices, unique=False)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="headed_department"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "departments"
        ordering = ["name"]

    def __str__(self):
        return self.name