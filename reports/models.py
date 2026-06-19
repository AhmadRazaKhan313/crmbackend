from django.db import models
from tenants.mixins import TenantModel


class DailyReport(TenantModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        REVIEWED = "reviewed", "Reviewed"
        FLAGGED = "flagged", "Flagged"

    employee = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="daily_reports"
    )
    reviewed_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reviewed_reports"
    )

    date = models.DateField()
    department = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)

    # Work Summary
    tasks_completed = models.TextField()
    leads_worked = models.TextField(blank=True)
    clients_handled = models.TextField(blank=True)
    problems_faced = models.TextField(blank=True)
    tomorrow_plan = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    # Stats
    total_leads = models.PositiveIntegerField(default=0)
    total_calls = models.PositiveIntegerField(default=0)
    total_conversions = models.PositiveIntegerField(default=0)

    manager_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "daily_reports"
        ordering = ["-date", "-created_at"]
        unique_together = ("employee", "date")

    def __str__(self):
        return f"{self.employee.full_name} — {self.date}"