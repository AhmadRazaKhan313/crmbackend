from rest_framework import serializers
from .models import Department
from authentication.models import User


class DepartmentSerializer(serializers.ModelSerializer):
    head_name  = serializers.CharField(source="head.full_name", read_only=True)
    head_email = serializers.CharField(source="head.email",     read_only=True)

    employee_count = serializers.SerializerMethodField()
    lead_count     = serializers.SerializerMethodField()
    client_count   = serializers.SerializerMethodField()
    active_tasks   = serializers.SerializerMethodField()

    class Meta:
        model  = Department
        fields = (
            "id", "name", "type", "description",
            "head", "head_name", "head_email",
            "is_active", "created_at",
            "employee_count", "lead_count",
            "client_count", "active_tasks",
        )
        read_only_fields = ("id", "created_at")

    def get_employee_count(self, obj):
        return User.objects.filter(
            tenant     = obj.tenant,
            department = obj.type,
            is_active  = True
        ).count()

    def get_lead_count(self, obj):
        from leads.models import Lead
        return Lead.objects.filter(
            tenant      = obj.tenant,
            department  = obj.type,
            is_archived = False
        ).count()

    def get_client_count(self, obj):
        from clients.models import Client
        return Client.objects.filter(
            tenant      = obj.tenant,
            department  = obj.type,
            is_archived = False
        ).count()

    def get_active_tasks(self, obj):
        from tasks.models import Task
        # ✅ FIX: is_archived=False add kiya — archived tasks count nahi hongi
        return Task.objects.filter(
            tenant      = obj.tenant,
            department  = obj.type,
            is_archived = False,
            status__in  = ("pending", "in_progress")
        ).count()