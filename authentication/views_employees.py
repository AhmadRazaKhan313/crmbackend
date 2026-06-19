from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import User
from .serializers_employees import (
    EmployeeListSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
)
from core.permissions import IsDeptHeadOrAbove
from core.models import UserRole, Role


class EmployeeListCreateView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def get(self, request):
        qs = User.objects.filter(
            tenant=request.user.tenant,
            is_super_admin=False
        ).select_related("tenant").prefetch_related("assigned_roles__role")

        department = request.query_params.get("department")
        role       = request.query_params.get("role")
        search     = request.query_params.get("search")

        if department: qs = qs.filter(department=department)
        if role:       qs = qs.filter(role=role)
        if search:
            qs = qs.filter(full_name__icontains=search) | qs.filter(email__icontains=search)

        if request.user.role == "dept_head":
            qs = qs.filter(department=request.user.department)

        return Response(EmployeeListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = EmployeeCreateSerializer(
            data=request.data,
            context={"request": request, "tenant": request.user.tenant}
        )
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(EmployeeListSerializer(employee).data, status=status.HTTP_201_CREATED)


class EmployeeDetailView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def _get_employee(self, pk, tenant):
        return get_object_or_404(User, pk=pk, tenant=tenant, is_super_admin=False)

    def get(self, request, pk):
        emp = self._get_employee(pk, request.user.tenant)
        return Response(EmployeeListSerializer(emp).data)

    def patch(self, request, pk):
        emp        = self._get_employee(pk, request.user.tenant)
        serializer = EmployeeUpdateSerializer(emp, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        emp.refresh_from_db()
        return Response(EmployeeListSerializer(emp).data)

    def delete(self, request, pk):
        if not (request.user.is_super_admin or request.user.role in ("ceo", "coo")):
            return Response(
                {"detail": "Only CEO/COO can deactivate employees."},
                status=status.HTTP_403_FORBIDDEN
            )
        emp = self._get_employee(pk, request.user.tenant)
        emp.is_active = False
        emp.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeRoleAssignView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def post(self, request, pk):
        emp     = get_object_or_404(User, pk=pk, tenant=request.user.tenant)
        role_id = request.data.get("role_id")
        role    = get_object_or_404(Role, pk=role_id, tenant=request.user.tenant)
        user_role, created = UserRole.objects.get_or_create(
            user=emp, role=role,
            defaults={"assigned_by": request.user}
        )
        if not created:
            return Response(
                {"detail": "Role already assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"detail": "Role assigned successfully."}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        emp     = get_object_or_404(User, pk=pk, tenant=request.user.tenant)
        role_id = request.data.get("role_id")
        UserRole.objects.filter(user=emp, role_id=role_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminPasswordResetView(APIView):
    permission_classes = (IsDeptHeadOrAbove,)

    def post(self, request, pk):
        emp          = get_object_or_404(User, pk=pk, tenant=request.user.tenant, is_super_admin=False)
        new_password = request.data.get("new_password", "")

        if len(new_password) < 8:
            return Response(
                {"detail": "Password must be at least 8 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        emp.set_password(new_password)
        emp.save()
        return Response({"detail": f"Password reset successfully for {emp.full_name}."})