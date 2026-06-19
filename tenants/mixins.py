from django.db import models
from django.conf import settings


class TenantModel(models.Model):
    """
    Sab tenant-specific models is se inherit karein.
    tenant field automatically set hoti hai.
    """
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s",
        db_index=True,
    )

    class Meta:
        abstract = True