from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Permission, Role, UserRole
from .serializers import (
    PermissionSerializer, RoleSerializer,
    AssignRoleSerializer, UserRoleSerializer
)
from .permissions import IsCEOOrAbove, IsManagerOrAbove, IsDeptHeadOrAbove


class PermissionListView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def get(self, request):
        perms  = Permission.objects.all()
        module = request.query_params.get("module")
        if module:
            perms = perms.filter(module=module)
        return Response(PermissionSerializer(perms, many=True).data)


class RoleListCreateView(APIView):
    permission_classes = (IsCEOOrAbove,)

    def get(self, request):
        # System roles + tenant custom roles dono show karo
        roles = Role.objects.filter(
            Q(tenant=request.user.tenant) | Q(is_system=True)
        ).prefetch_related("permissions").order_by("-is_system", "name")
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tenant=request.user.tenant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = (IsCEOOrAbove,)

    def _get_role(self, pk, tenant):
        # System roles edit/delete nahi ho sakti
        return get_object_or_404(Role, pk=pk, tenant=tenant, is_system=False)

    def get(self, request, pk):
        # System roles view kar sakte hain
        role = get_object_or_404(
            Role.objects.filter(
                Q(tenant=request.user.tenant) | Q(is_system=True)
            ), pk=pk
        )
        return Response(RoleSerializer(role).data)

    def patch(self, request, pk):
        role       = self._get_role(pk, request.user.tenant)
        serializer = RoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        role = self._get_role(pk, request.user.tenant)
        if role.assigned_users.exists():
            return Response(
                {"detail": "Cannot delete role with assigned users."},
                status=status.HTTP_400_BAD_REQUEST
            )
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AssignRoleView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def post(self, request):
        serializer = AssignRoleSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        role = serializer.validated_data["role"]
        user_role, created = UserRole.objects.get_or_create(
            user=user, role=role,
            defaults={"assigned_by": request.user}
        )
        if not created:
            return Response(
                {"detail": "Role already assigned to this user."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(UserRoleSerializer(user_role).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        user_id = request.data.get("user_id")
        role_id = request.data.get("role_id")
        UserRole.objects.filter(
            user_id=user_id,
            role_id=role_id,
            user__tenant=request.user.tenant
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserRolesView(APIView):
    permission_classes = (IsManagerOrAbove,)

    def get(self, request, user_id):
        roles = UserRole.objects.filter(
            user_id=user_id,
            user__tenant=request.user.tenant
        ).select_related("role", "user")
        return Response(UserRoleSerializer(roles, many=True).data)
