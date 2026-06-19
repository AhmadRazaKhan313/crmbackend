from django.db import models
from tenants.mixins import TenantModel


class Task(TenantModel):
    class Priority(models.TextChoices):
        LOW    = "low",    "Low"
        MEDIUM = "medium", "Medium"
        HIGH   = "high",   "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        PENDING     = "pending",     "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED   = "completed",   "Completed"
        DELAYED     = "delayed",     "Delayed"

    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status      = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    department  = models.CharField(max_length=20, blank=True)

    assigned_to = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="assigned_tasks"
    )
    assigned_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks"
    )

    due_date     = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes       = models.TextField(blank=True)
    attachments = models.FileField(upload_to="tasks/", blank=True, null=True)

    # ✅ Soft delete — hard delete ki jagah
    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class TaskComment(models.Model):
    task       = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    comment    = models.TextField()
    created_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = "task_comments"
        ordering  = ["created_at"]