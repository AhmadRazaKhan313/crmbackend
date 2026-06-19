from django.db import models
from tenants.mixins import TenantModel


class Notification(TenantModel):
    class Type(models.TextChoices):
        LEAD_ASSIGNED    = "lead_assigned",    "Lead Assigned"
        LEAD_CONVERTED   = "lead_converted",   "Lead Converted"
        TASK_ASSIGNED    = "task_assigned",    "Task Assigned"
        TASK_DUE         = "task_due",         "Task Due"
        CLIENT_ASSIGNED  = "client_assigned",  "Client Assigned"
        LEAVE_APPROVED   = "leave_approved",   "Leave Approved"
        LEAVE_REJECTED   = "leave_rejected",   "Leave Rejected"
        REPORT_REVIEWED  = "report_reviewed",  "Report Reviewed"
        GENERAL          = "general",          "General"

    recipient  = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    type       = models.CharField(max_length=30, choices=Type.choices)
    title      = models.CharField(max_length=200)
    message    = models.TextField(blank=True)
    link       = models.CharField(max_length=200, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
