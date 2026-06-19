from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import DailyReport
from .serializers import (
    DailyReportListSerializer, DailyReportDetailSerializer,
    DailyReportCreateSerializer, ReportReviewSerializer
)
from core.permissions import IsAnyEmployee, IsManagerOrAbove, FeatureRequired
from notifications.utils import notify

FEATURE = FeatureRequired("reports_module")

# ✅ FIX: Sirf yeh fields employee update kar sakta hai
REPORT_PATCH_ALLOWED = {
    "tasks_completed", "leads_worked", "clients_handled",
    "problems_faced", "tomorrow_plan", "notes",
    "total_leads", "total_calls", "total_conversions",
}


class DailyReportListCreateView(APIView):
    permission_classes = (IsAnyEmployee, FEATURE)

    def get(self, request):
        qs = DailyReport.objects.filter(
            tenant=request.user.tenant
        ).select_related("employee", "reviewed_by")

        date        = request.query_params.get("date")
        dept        = request.query_params.get("department")
        status_f    = request.query_params.get("status")
        employee_id = request.query_params.get("employee")

        if date:        qs = qs.filter(date=date)
        if dept:        qs = qs.filter(department=dept)
        if status_f:    qs = qs.filter(status=status_f)
        if employee_id: qs = qs.filter(employee_id=employee_id)

        if request.user.role in ("lead_employee", "sales_employee"):
            qs = qs.filter(employee=request.user)

        if request.user.role in ("lead_manager", "sales_manager"):
            qs = qs.filter(department=request.user.department)

        return Response(DailyReportListSerializer(qs, many=True).data)

    def post(self, request):
        serializer = DailyReportCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        return Response(DailyReportDetailSerializer(report).data, status=status.HTTP_201_CREATED)


class DailyReportDetailView(APIView):
    permission_classes = (IsAnyEmployee, FEATURE)

    def _get_report(self, pk, user):
        return get_object_or_404(DailyReport, pk=pk, tenant=user.tenant)

    def get(self, request, pk):
        return Response(DailyReportDetailSerializer(self._get_report(pk, request.user)).data)

    def patch(self, request, pk):
        report = self._get_report(pk, request.user)
        if report.employee != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        if report.status != "submitted":
            return Response({"detail": "Cannot edit reviewed report."}, status=status.HTTP_400_BAD_REQUEST)
        # ✅ FIX: setattr hataya — whitelist se safe update
        safe_data = {k: v for k, v in request.data.items() if k in REPORT_PATCH_ALLOWED}
        serializer = DailyReportCreateSerializer(
            report, data=safe_data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        report.refresh_from_db()
        return Response(DailyReportDetailSerializer(report).data)


class ReportReviewView(APIView):
    permission_classes = (IsManagerOrAbove, FEATURE)

    def post(self, request, pk):
        report = get_object_or_404(DailyReport, pk=pk, tenant=request.user.tenant)
        serializer = ReportReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report.status           = serializer.validated_data["status"]
        report.manager_feedback = serializer.validated_data.get("manager_feedback", "")
        report.reviewed_by      = request.user
        report.save()
        return Response(DailyReportDetailSerializer(report).data)