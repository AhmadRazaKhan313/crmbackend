from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from leads.models import Lead
from clients.models import Client, Payment
from tasks.models import Task
from authentication.models import User
from reports.models import DailyReport
from core.permissions import IsDeptHeadOrAbove, IsManagerOrAbove, FeatureRequired


class OverviewAnalyticsView(APIView):
    # FeatureRequired("analytics") — sirf wohi tenants access kar sakte hain
    # jinka analytics flag ON hai
    permission_classes = (IsAuthenticated, FeatureRequired("analytics"))

    def get(self, request):
        tenant = request.user.tenant
        today = timezone.now().date()
        month_start = today.replace(day=1)
        week_start = today - timedelta(days=today.weekday())

        lead_qs = Lead.objects.filter(tenant=tenant, is_archived=False)
        client_qs = Client.objects.filter(tenant=tenant, is_archived=False)
        task_qs = Task.objects.filter(tenant=tenant)
        user_qs = User.objects.filter(tenant=tenant, is_active=True)

        # dept filter
        if request.user.role in ("dept_head", "lead_manager", "sales_manager"):
            lead_qs = lead_qs.filter(department=request.user.department)
            client_qs = client_qs.filter(department=request.user.department)
            task_qs = task_qs.filter(department=request.user.department)
            user_qs = user_qs.filter(department=request.user.department)

        # Lead stats
        lead_stats = {
            "total": lead_qs.count(),
            "new": lead_qs.filter(status="new").count(),
            "contacted": lead_qs.filter(status="contacted").count(),
            "interested": lead_qs.filter(status="interested").count(),
            "converted": lead_qs.filter(status="converted").count(),
            "rejected": lead_qs.filter(status="rejected").count(),
            "this_month": lead_qs.filter(created_at__date__gte=month_start).count(),
            "this_week": lead_qs.filter(created_at__date__gte=week_start).count(),
            "today": lead_qs.filter(created_at__date=today).count(),
        }

        total = lead_stats["total"]
        lead_stats["conversion_rate"] = (
            round((lead_stats["converted"] / total) * 100, 1) if total else 0
        )

        client_stats = {
            "total": client_qs.count(),
            "active": client_qs.filter(status="active").count(),
            "completed": client_qs.filter(status="completed").count(),
            "this_month": client_qs.filter(created_at__date__gte=month_start).count(),
        }

        task_stats = {
            "total": task_qs.count(),
            "pending": task_qs.filter(status="pending").count(),
            "in_progress": task_qs.filter(status="in_progress").count(),
            "completed": task_qs.filter(status="completed").count(),
            "delayed": task_qs.filter(status="delayed").count(),
            "urgent": task_qs.filter(priority="urgent").count(),
        }

        employee_stats = {
            "total": user_qs.count(),
            "by_department": list(
                user_qs.values("department")
                .annotate(count=Count("id"))
                .order_by("department")
            ),
        }

        lead_by_source = list(
            lead_qs.values("source")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        lead_by_dept = list(
            lead_qs.values("department")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        monthly_leads = []
        for i in range(5, -1, -1):
            d = today - timedelta(days=30 * i)
            month = d.replace(day=1)
            count = lead_qs.filter(
                created_at__year=month.year,
                created_at__month=month.month
            ).count()
            monthly_leads.append({
                "month": month.strftime("%b"),
                "leads": count,
            })

        return Response({
            "leads": lead_stats,
            "clients": client_stats,
            "tasks": task_stats,
            "employees": employee_stats,
            "lead_by_source": lead_by_source,
            "lead_by_dept": lead_by_dept,
            "monthly_leads": monthly_leads,
        })


class KPIView(APIView):
    permission_classes = (IsManagerOrAbove, FeatureRequired("analytics"))

    def get(self, request):
        tenant = request.user.tenant
        today = timezone.now().date()
        month_start = today.replace(day=1)

        lead_qs = Lead.objects.filter(tenant=tenant, is_archived=False)
        if request.user.role in ("lead_manager", "sales_manager"):
            lead_qs = lead_qs.filter(department=request.user.department)

        total_leads = lead_qs.count()
        converted = lead_qs.filter(status="converted").count()
        monthly_leads = lead_qs.filter(created_at__date__gte=month_start).count()

        employees = User.objects.filter(
            tenant=tenant,
            is_active=True,
            role__in=("lead_employee", "sales_employee")
        )
        if request.user.role in ("lead_manager", "sales_manager"):
            employees = employees.filter(department=request.user.department)

        employee_kpis = []
        for emp in employees:
            emp_leads = lead_qs.filter(assigned_to=emp)
            emp_converted = emp_leads.filter(status="converted").count()
            emp_total = emp_leads.count()
            reports = DailyReport.objects.filter(
                employee=emp,
                date__gte=month_start
            ).count()
            employee_kpis.append({
                "name": emp.full_name,
                "role": emp.get_role_display(),
                "department": emp.department,
                "total_leads": emp_total,
                "converted": emp_converted,
                "conversion_rate": round((emp_converted / emp_total) * 100, 1) if emp_total else 0,
                "reports_submitted": reports,
            })

        return Response({
            "summary": {
                "total_leads": total_leads,
                "converted": converted,
                "conversion_rate": round((converted / total_leads) * 100, 1) if total_leads else 0,
                "monthly_leads": monthly_leads,
            },
            "employee_kpis": sorted(employee_kpis, key=lambda x: x["converted"], reverse=True),
        })