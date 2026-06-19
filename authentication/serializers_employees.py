from rest_framework import serializers
from .models import User
from core.models import Role, UserRole


class EmployeeListSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    assigned_roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "full_name", "email", "phone", "role",
            "role_display", "department", "employee_id",
            "avatar", "is_active", "created_at", "assigned_roles"
        )

    def get_assigned_roles(self, obj):
        return list(
            obj.assigned_roles.select_related("role")
            .values_list("role__name", flat=True)
        )


class EmployeeCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Role.objects.all(),
        required=False
    )

    class Meta:
        model = User
        fields = (
            "full_name", "email", "phone", "password",
            "role", "department", "avatar", "role_ids"
        )

    def create(self, validated_data):
        role_ids = validated_data.pop("role_ids", [])
        tenant = self.context["tenant"]
        user = User.objects.create_user(**validated_data)
        user.tenant = tenant
        user.save()
        for role in role_ids:
            UserRole.objects.create(
                user=user,
                role=role,
                assigned_by=self.context["request"].user
            )
        return user


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "full_name", "phone", "role",
            "department", "avatar", "is_active"
        )