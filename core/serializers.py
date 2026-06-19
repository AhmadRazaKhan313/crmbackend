from rest_framework import serializers
from .models import Permission, Role, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Permission
        fields = ("id", "module", "action", "codename", "label")


class RoleSerializer(serializers.ModelSerializer):
    permissions    = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True,
        queryset=Permission.objects.all(),
        source="permissions",
        required=False,
    )
    user_count = serializers.SerializerMethodField()

    class Meta:
        model  = Role
        fields = (
            "id", "name", "description",
            "permissions", "permission_ids",
            "user_count", "is_system", "created_at",
        )
        read_only_fields = ("id", "is_system", "created_at")

    def get_user_count(self, obj):
        if obj.is_system:
            return "—"
        return obj.assigned_users.count()


class AssignRoleSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_id = serializers.IntegerField()

    def validate(self, data):
        from authentication.models import User
        request = self.context["request"]
        try:
            data["user"] = User.objects.get(pk=data["user_id"], tenant=request.user.tenant)
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "User not found."})
        try:
            data["role"] = Role.objects.get(pk=data["role_id"], tenant=request.user.tenant)
        except Role.DoesNotExist:
            raise serializers.ValidationError({"role_id": "Role not found."})
        return data


class UserRoleSerializer(serializers.ModelSerializer):
    role_name        = serializers.CharField(source="role.name",             read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.full_name", read_only=True)

    class Meta:
        model  = UserRole
        fields = ("id", "role", "role_name", "assigned_by_name", "assigned_at")
