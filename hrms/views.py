from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import date, timedelta
import calendar

from authentication.models import User
from core.permissions import (
    IsCEOOrAbove, IsCOOOrAbove, IsDeptHeadOrAbove,
    IsManagerOrAbove, IsAnyEmployee, FeatureRequired
)
from core.mixins import TenantQuerysetMixin
from .models import (
    Shift, EmployeeShift, Attendance,
    LeaveType, LeaveRequest, LeaveBalance,
    SalaryStructure, PayrollRun, PaySlip
)
from .serializers import (
    ShiftSerializer, EmployeeShiftSerializer,
    AttendanceSerializer, CheckInSerializer, CheckOutSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer,
    LeaveBalanceSerializer, LeaveApprovalSerializer,
    SalaryStructureSerializer, PayrollRunSerializer, PaySlipSerializer
)

FEATURE = FeatureRequired("hrms")


# ─── Helper ──────────────────────────────────────────────────

def tenant_qs(model, user):
    if user.is_super_admin:
        return model.objects.all()
    return model.objects.filter(tenant=user.tenant)


def can_approve_leave(user):
    """CEO, COO, Dept Head sab approve kar sakte hain"""
    return user.role in ("ceo", "coo", "dept_head") or user.is_super_admin


# ─── SHIFT VIEWS ─────────────────────────────────────────────

class ShiftListCreateView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        qs = tenant_qs(Shift, request.user).filter(is_active=True)
        return Response(ShiftSerializer(qs, many=True).data)

    def post(self, request):
        if not IsDeptHeadOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        s = ShiftSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(tenant=request.user.tenant)
        return Response(s.data, status=201)


class ShiftDetailView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get_object(self, request, pk):
        return get_object_or_404(tenant_qs(Shift, request.user), pk=pk)

    def get(self, request, pk):
        return Response(ShiftSerializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        if not IsDeptHeadOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        obj = self.get_object(request, pk)
        s = ShiftSerializer(obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        if not IsDeptHeadOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        obj = self.get_object(request, pk)
        obj.is_active = False
        obj.save()
        return Response(status=204)


class AssignShiftView(APIView):
    """Employee ko shift assign karna"""
    permission_classes = (IsAuthenticated, FEATURE)

    def post(self, request):
        if not IsDeptHeadOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        s = EmployeeShiftSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        emp_id = request.data.get("employee")
        shift_id = request.data.get("shift")
        emp = get_object_or_404(User, pk=emp_id, tenant=request.user.tenant)
        shift = get_object_or_404(Shift, pk=shift_id, tenant=request.user.tenant)
        obj, _ = EmployeeShift.objects.update_or_create(
            employee=emp,
            defaults={
                "shift": shift,
                "tenant": request.user.tenant,
                "effective_from": request.data.get("effective_from", date.today()),
                "assigned_by": request.user,
            }
        )
        return Response(EmployeeShiftSerializer(obj).data, status=201)


# ─── ATTENDANCE VIEWS ─────────────────────────────────────────

class AttendanceListView(APIView):
    """
    GET — Manager/Head: apni team ki attendance
          Employee: apni khud ki
    """
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        qs = tenant_qs(Attendance, request.user)

        # Filters
        emp_id = request.query_params.get("employee")
        dept = request.query_params.get("department")
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        month = request.query_params.get("month")
        year = request.query_params.get("year")

        # Employee sirf apni dekh sakta hai
        if request.user.role in ("lead_employee", "sales_employee"):
            qs = qs.filter(employee=request.user)
        elif emp_id:
            qs = qs.filter(employee_id=emp_id)

        if dept:
            qs = qs.filter(employee__department=dept)
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)

        qs = qs.select_related("employee", "marked_by").order_by("-date")
        return Response(AttendanceSerializer(qs, many=True).data)

    def post(self, request):
        """Manager manually attendance mark kare"""
        if not IsManagerOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        s = AttendanceSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        emp = get_object_or_404(User, pk=request.data.get("employee"), tenant=request.user.tenant)
        s.save(tenant=request.user.tenant, employee=emp, marked_by=request.user)
        return Response(s.data, status=201)


class MyAttendanceCheckInView(APIView):
    """Employee apna check-in kare"""
    permission_classes = (IsAuthenticated, FEATURE)

    def post(self, request):
        today = date.today()
        now = timezone.now()

        # Agar aaj already check-in hai to block karo
        existing = Attendance.objects.filter(
            employee=request.user, date=today
        ).first()

        if existing and existing.check_in:
            return Response(
                {"detail": "Already checked in today."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Late check karo shift se
        late_minutes = 0
        try:
            shift = request.user.shift_assignment.shift
            if shift:
                from datetime import datetime, timezone as dt_tz
                shift_start = timezone.make_aware(
                    datetime.combine(today, shift.start_time)
                )
                if now > shift_start:
                    late_minutes = int((now - shift_start).total_seconds() / 60)
        except Exception:
            pass

        att_status = Attendance.Status.LATE if late_minutes > 0 else Attendance.Status.PRESENT

        if existing:
            existing.check_in = now
            existing.late_minutes = late_minutes
            existing.status = att_status
            if request.data.get("notes"):
                existing.notes = request.data["notes"]
            existing.save()
            obj = existing
        else:
            obj = Attendance.objects.create(
                tenant=request.user.tenant,
                employee=request.user,
                date=today,
                check_in=now,
                late_minutes=late_minutes,
                status=att_status,
                notes=request.data.get("notes", ""),
            )

        return Response(AttendanceSerializer(obj).data, status=201)


class MyAttendanceCheckOutView(APIView):
    """Employee apna check-out kare"""
    permission_classes = (IsAuthenticated, FEATURE)

    def post(self, request):
        today = date.today()
        now = timezone.now()

        att = Attendance.objects.filter(
            employee=request.user, date=today
        ).first()

        if not att or not att.check_in:
            return Response(
                {"detail": "No check-in found for today."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if att.check_out:
            return Response(
                {"detail": "Already checked out today."},
                status=status.HTTP_400_BAD_REQUEST
            )

        att.check_out = now
        if request.data.get("notes"):
            att.notes = (att.notes + "\n" + request.data["notes"]).strip()

        # Overtime check
        try:
            shift = request.user.shift_assignment.shift
            if shift:
                from datetime import datetime
                shift_end = timezone.make_aware(
                    datetime.combine(today, shift.end_time)
                )
                if now > shift_end:
                    att.overtime_minutes = int((now - shift_end).total_seconds() / 60)
        except Exception:
            pass

        att.save()
        return Response(AttendanceSerializer(att).data)


class TodayAttendanceView(APIView):
    """Aaj ki summary — manager ke liye"""
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        today = date.today()
        qs = tenant_qs(Attendance, request.user).filter(date=today)

        if request.user.role in ("dept_head", "lead_manager", "sales_manager"):
            qs = qs.filter(employee__department=request.user.department)

        by_status = {}
        for a in qs:
            by_status[a.status] = by_status.get(a.status, 0) + 1

        total_employees = tenant_qs(User, request.user).filter(
            is_active=True,
            tenant=request.user.tenant if not request.user.is_super_admin else None
        ).exclude(is_super_admin=True).count()

        return Response({
            "date": today,
            "total_employees": total_employees,
            "marked": qs.count(),
            "by_status": by_status,
            "records": AttendanceSerializer(
                qs.select_related("employee"), many=True
            ).data
        })


# ─── LEAVE VIEWS ─────────────────────────────────────────────

class LeaveTypeListView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        qs = tenant_qs(LeaveType, request.user).filter(is_active=True)
        return Response(LeaveTypeSerializer(qs, many=True).data)

    def post(self, request):
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        s = LeaveTypeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(tenant=request.user.tenant)
        return Response(s.data, status=201)


class LeaveRequestListCreateView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        qs = tenant_qs(LeaveRequest, request.user)

        # Employee: apni hi requests
        if request.user.role in ("lead_employee", "sales_employee"):
            qs = qs.filter(employee=request.user)
        else:
            emp_id = request.query_params.get("employee")
            dept = request.query_params.get("department")
            status_filter = request.query_params.get("status")
            if emp_id:
                qs = qs.filter(employee_id=emp_id)
            if dept:
                qs = qs.filter(employee__department=dept)
            if status_filter:
                qs = qs.filter(status=status_filter)

        qs = qs.select_related("employee", "leave_type", "reviewed_by")
        return Response(LeaveRequestSerializer(qs, many=True).data)

    def post(self, request):
        """Employee leave apply kare"""
        s = LeaveRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        leave_type = get_object_or_404(
            LeaveType, pk=request.data.get("leave_type"), tenant=request.user.tenant
        )

        # Balance check
        year = date.today().year
        balance, _ = LeaveBalance.objects.get_or_create(
            employee=request.user,
            leave_type=leave_type,
            year=year,
            defaults={"tenant": request.user.tenant, "allocated": leave_type.max_days_per_year}
        )
        total_days = s.validated_data.get("total_days", 1)
        if balance.remaining < total_days:
            return Response(
                {"detail": f"Insufficient leave balance. Remaining: {balance.remaining} days."},
                status=400
            )

        obj = s.save(
            tenant=request.user.tenant,
            employee=request.user,
            leave_type=leave_type,
        )
        return Response(LeaveRequestSerializer(obj).data, status=201)


class LeaveRequestDetailView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get_object(self, request, pk):
        return get_object_or_404(tenant_qs(LeaveRequest, request.user), pk=pk)

    def get(self, request, pk):
        return Response(LeaveRequestSerializer(self.get_object(request, pk)).data)

    def delete(self, request, pk):
        """Employee apni pending request cancel kar sake"""
        obj = self.get_object(request, pk)
        if obj.employee != request.user:
            return Response({"detail": "Permission denied."}, status=403)
        if obj.status != "pending":
            return Response({"detail": "Only pending requests can be cancelled."}, status=400)
        obj.status = "cancelled"
        obj.save()
        return Response(status=204)


class LeaveApprovalView(APIView):
    """CEO, COO, Dept Head — leave approve/reject kare"""
    permission_classes = (IsAuthenticated, FEATURE)

    def post(self, request, pk):
        if not can_approve_leave(request.user):
            return Response({"detail": "Permission denied."}, status=403)

        obj = get_object_or_404(tenant_qs(LeaveRequest, request.user), pk=pk)
        if obj.status != "pending":
            return Response({"detail": "Only pending requests can be reviewed."}, status=400)

        s = LeaveApprovalSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        obj.status = s.validated_data["action"]
        obj.reviewed_by = request.user
        obj.reviewed_at = timezone.now()
        if s.validated_data["action"] == "rejected":
            obj.rejection_reason = s.validated_data.get("rejection_reason", "")

        obj.save()

        # Balance deduct karo agar approved
        if obj.status == "approved":
            year = obj.from_date.year
            balance, _ = LeaveBalance.objects.get_or_create(
                employee=obj.employee,
                leave_type=obj.leave_type,
                year=year,
                defaults={
                    "tenant": obj.tenant,
                    "allocated": obj.leave_type.max_days_per_year
                }
            )
            balance.used = min(balance.used + obj.total_days, balance.allocated)
            balance.save()

        return Response(LeaveRequestSerializer(obj).data)


class LeaveBalanceView(APIView):
    """Employee ki leave balance dekho"""
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        emp_id = request.query_params.get("employee", request.user.pk)

        # Employees sirf apni dekh sakte hain
        if request.user.role in ("lead_employee", "sales_employee"):
            emp_id = request.user.pk

        emp = get_object_or_404(User, pk=emp_id, tenant=request.user.tenant)

        # Ensure balances exist for all leave types
        leave_types = tenant_qs(LeaveType, request.user).filter(is_active=True)
        balances = []
        for lt in leave_types:
            b, _ = LeaveBalance.objects.get_or_create(
                employee=emp, leave_type=lt, year=year,
                defaults={"tenant": request.user.tenant, "allocated": lt.max_days_per_year}
            )
            balances.append(b)

        return Response(LeaveBalanceSerializer(balances, many=True).data)


# ─── PAYROLL VIEWS ────────────────────────────────────────────

class SalaryStructureView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        """List all salary structures — CEO/COO only"""
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        qs = tenant_qs(SalaryStructure, request.user).select_related("employee")
        return Response(SalaryStructureSerializer(qs, many=True).data)

    def post(self, request):
        """Create/update salary structure for an employee"""
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        emp = get_object_or_404(
            User, pk=request.data.get("employee"), tenant=request.user.tenant
        )
        obj, created = SalaryStructure.objects.get_or_create(
            employee=emp,
            defaults={"tenant": request.user.tenant}
        )
        s = SalaryStructureSerializer(obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data, status=201 if created else 200)


class EmployeeSalaryView(APIView):
    """Single employee ki salary"""
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request, emp_id):
        # Employees sirf apni dekh sakte hain
        if request.user.role in ("lead_employee", "sales_employee"):
            if str(request.user.pk) != str(emp_id):
                return Response({"detail": "Permission denied."}, status=403)
        emp = get_object_or_404(User, pk=emp_id, tenant=request.user.tenant)
        obj = get_object_or_404(SalaryStructure, employee=emp)
        return Response(SalaryStructureSerializer(obj).data)


class PayrollRunListView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        qs = tenant_qs(PayrollRun, request.user)
        return Response(PayrollRunSerializer(qs, many=True).data)

    def post(self, request):
        """New payroll run generate karo"""
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)

        month = int(request.data.get("month", date.today().month))
        year = int(request.data.get("year", date.today().year))

        if PayrollRun.objects.filter(tenant=request.user.tenant, month=month, year=year).exists():
            return Response(
                {"detail": f"Payroll for {month}/{year} already exists."},
                status=400
            )

        run = PayrollRun.objects.create(
            tenant=request.user.tenant,
            month=month, year=year,
            generated_by=request.user,
            notes=request.data.get("notes", ""),
        )

        # Generate payslips for all active employees
        employees = User.objects.filter(
            tenant=request.user.tenant, is_active=True
        ).exclude(is_super_admin=True)

        # Get month attendance summary
        _, days_in_month = calendar.monthrange(year, month)

        slips_created = 0
        for emp in employees:
            try:
                salary = emp.salary_structure
            except SalaryStructure.DoesNotExist:
                continue  # No salary defined — skip

            # Attendance this month
            att_qs = Attendance.objects.filter(
                employee=emp, date__month=month, date__year=year
            )
            days_present = att_qs.filter(
                status__in=["present", "late", "half_day"]
            ).count()
            days_absent = att_qs.filter(status="absent").count()
            overtime_mins = att_qs.aggregate(t=Sum("overtime_minutes"))["t"] or 0

            # Per-day salary for deductions
            daily_salary = float(salary.gross_salary) / days_in_month if days_in_month else 0
            leave_deduction = round(days_absent * daily_salary, 2)
            overtime_bonus = round((overtime_mins / 60) * (daily_salary / 8), 2)

            net = float(salary.net_salary) - leave_deduction + overtime_bonus

            PaySlip.objects.create(
                tenant=request.user.tenant,
                payroll_run=run,
                employee=emp,
                basic_salary=salary.basic_salary,
                house_allowance=salary.house_allowance,
                transport_allowance=salary.transport_allowance,
                medical_allowance=salary.medical_allowance,
                other_allowances=salary.other_allowances,
                tax_deduction=salary.tax_deduction,
                provident_fund=salary.provident_fund,
                other_deductions=salary.other_deductions,
                days_present=days_present,
                days_absent=days_absent,
                leave_deduction=leave_deduction,
                overtime_bonus=overtime_bonus,
                gross_salary=salary.gross_salary,
                total_deductions=float(salary.total_deductions) + leave_deduction,
                net_salary=round(net, 2),
            )
            slips_created += 1

        run.status = "processed"
        run.save()

        return Response(PayrollRunSerializer(run).data, status=201)


class PayrollRunDetailView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request, pk):
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        run = get_object_or_404(tenant_qs(PayrollRun, request.user), pk=pk)
        return Response(PayrollRunSerializer(run).data)

    def patch(self, request, pk):
        """Mark as paid"""
        if not IsCOOOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)
        run = get_object_or_404(tenant_qs(PayrollRun, request.user), pk=pk)
        new_status = request.data.get("status")
        if new_status == "paid":
            run.status = "paid"
            run.slips.all().update(is_paid=True, paid_at=timezone.now())
            run.save()
        return Response(PayrollRunSerializer(run).data)


class MyPaySlipsView(APIView):
    """Employee apni payslips dekhe"""
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        qs = PaySlip.objects.filter(
            employee=request.user
        ).select_related("payroll_run").order_by(
            "-payroll_run__year", "-payroll_run__month"
        )
        return Response(PaySlipSerializer(qs, many=True).data)


# ─── HRMS DASHBOARD ──────────────────────────────────────────

class HRMSDashboardView(APIView):
    permission_classes = (IsAuthenticated, FEATURE)

    def get(self, request):
        if not IsDeptHeadOrAbove().has_permission(request, self):
            return Response({"detail": "Permission denied."}, status=403)

        today = date.today()
        tenant = request.user.tenant

        emp_qs = User.objects.filter(tenant=tenant, is_active=True).exclude(is_super_admin=True)
        if request.user.role == "dept_head":
            emp_qs = emp_qs.filter(department=request.user.department)

        # Today attendance
        att_today = Attendance.objects.filter(
            tenant=tenant, date=today,
            employee__in=emp_qs
        )

        # Pending leaves
        pending_leaves = LeaveRequest.objects.filter(
            tenant=tenant, status="pending",
            employee__in=emp_qs
        ).count()

        # This month attendance summary
        month_att = Attendance.objects.filter(
            tenant=tenant,
            date__month=today.month,
            date__year=today.year,
            employee__in=emp_qs
        )

        return Response({
            "total_employees": emp_qs.count(),
            "today": {
                "present": att_today.filter(status__in=["present", "late"]).count(),
                "absent": att_today.filter(status="absent").count(),
                "on_leave": att_today.filter(status="on_leave").count(),
                "not_marked": emp_qs.count() - att_today.count(),
            },
            "pending_leave_requests": pending_leaves,
            "this_month": {
                "avg_present": round(
                    month_att.filter(status__in=["present", "late"]).count() / max(emp_qs.count(), 1), 1
                ),
                "total_absent": month_att.filter(status="absent").count(),
                "total_late": month_att.filter(status="late").count(),
                "total_overtime_hours": round(
                    (month_att.aggregate(t=Sum("overtime_minutes"))["t"] or 0) / 60, 1
                ),
            }
        })
