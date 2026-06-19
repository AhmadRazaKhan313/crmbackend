from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Tenant, TenantFeature
from .serializers import TenantSerializer, TenantRegisterSerializer, TenantFeatureSerializer
from authentication.serializers import RegisterSerializer, UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from core.permissions import IsSuperAdmin


# ─────────────────────────────────────────────
# Public — Tenant Register
# ─────────────────────────────────────────────

class TenantRegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        t_serializer = TenantRegisterSerializer(data=request.data)
        t_serializer.is_valid(raise_exception=True)
        tenant = t_serializer.save()

        user_data = {
            "email": request.data.get("email"),
            "full_name": request.data.get("admin_name", "Admin"),
            "password": request.data.get("password"),
            "role": "ceo",
        }
        u_serializer = RegisterSerializer(data=user_data)
        u_serializer.is_valid(raise_exception=True)
        user = u_serializer.save()
        user.tenant = tenant
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "tenant": TenantSerializer(tenant).data,
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────
# Authenticated — Current Tenant
# ─────────────────────────────────────────────

class TenantDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response({"detail": "No tenant."}, status=404)
        return Response(TenantSerializer(tenant).data)

    def patch(self, request):
        tenant = request.user.tenant
        if not tenant:
            return Response({"detail": "No tenant."}, status=404)
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ─────────────────────────────────────────────
# Super Admin — All Tenants Management
# ─────────────────────────────────────────────

class SuperAdminStatsView(APIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        total = Tenant.objects.count()
        by_status = dict(
            Tenant.objects.values_list("status")
            .annotate(c=Count("id"))
            .values_list("status", "c")
        )
        by_plan = dict(
            Tenant.objects.values_list("plan")
            .annotate(c=Count("id"))
            .values_list("plan", "c")
        )
        return Response({
            "total_tenants": total,
            "by_status": by_status,
            "by_plan": by_plan,
        })


class SuperAdminTenantListView(APIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request):
        tenants = Tenant.objects.select_related("features").all()
        return Response(TenantSerializer(tenants, many=True).data)


class SuperAdminTenantDetailView(APIView):
    permission_classes = (IsSuperAdmin,)

    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        return Response(TenantSerializer(tenant).data)

    def patch(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TenantSerializer(tenant).data)


class SuperAdminFeatureFlagView(APIView):
    """
    Super Admin se specific tenant ke feature flags update karo.
    PATCH /tenant/admin/tenants/<id>/features/
    Body: { "analytics": true, "hrms": false, ... }
    """
    permission_classes = (IsSuperAdmin,)

    def get(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        features, _ = TenantFeature.objects.get_or_create(tenant=tenant)
        return Response(TenantFeatureSerializer(features).data)

    def patch(self, request, tenant_id):
        tenant = get_object_or_404(Tenant, id=tenant_id)
        features, _ = TenantFeature.objects.get_or_create(tenant=tenant)
        serializer = TenantFeatureSerializer(features, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
