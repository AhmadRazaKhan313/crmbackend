from rest_framework import serializers
from .models import Task, TaskComment


class TaskCommentSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = TaskComment
        fields = ("id", "comment", "created_by_name", "created_at")


class TaskListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.full_name", read_only=True)

    class Meta:
        model = Task
        fields = (
            "id", "title", "priority", "status", "department",
            "assigned_to_name", "assigned_by_name",
            "due_date", "created_at"
        )


class TaskDetailSerializer(serializers.ModelSerializer):
    comments = TaskCommentSerializer(many=True, read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.full_name", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        exclude = ("tenant", "assigned_by", "completed_at")

    def create(self, validated_data):
        request = self.context["request"]
        return Task.objects.create(
            tenant=request.user.tenant,
            assigned_by=request.user,
            **validated_data
        )