from rest_framework import serializers
from django.utils import timezone
from .models import (
    Shift, EmployeeShift, Attendance,
    LeaveType, LeaveRequest, LeaveBalance,
    SalaryStructure, PayrollRun, PaySlip
)


# ─── Mini User serializer (nested use ke liye) ───────────────

class MiniUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    employee_id = serializers.CharField()
    role = serializers.CharField()
    department = serializers.CharField()
    avatar = serializers.ImageField(required=False)


# ─── SHIFT ───────────────────────────────────────────────────

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        exclude = ("tenant",)
        read_only_fields = ("id", "created_at")


class EmployeeShiftSerializer(serializers.ModelSerializer):
    employee_detail = MiniUserSerializer(source="employee", read_only=True)
    shift_detail = ShiftSerializer(source="shift", read_only=True)

    class Meta:
        model = EmployeeShift
        exclude = ("tenant",)
        read_only_fields = ("id", "assigned_by")


# ─── ATTENDANCE ───────────────────────────────────────────────

class AttendanceSerializer(serializers.ModelSerializer):
    employee_detail = MiniUserSerializer(source="employee", read_only=True)
    working_hours = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        exclude = ("tenant",)
        read_only_fields = ("id", "working_minutes", "created_at", "updated_at", "marked_by")

    def get_working_hours(self, obj):
        if obj.working_minutes == 0:
            return "0h 0m"
        h = obj.working_minutes // 60
        m = obj.working_minutes % 60
        return f"{h}h {m}m"


class CheckInSerializer(serializers.Serializer):
    """Employee apna check-in kare"""
    notes = serializers.CharField(required=False, allow_blank=True)


class CheckOutSerializer(serializers.Serializer):
    """Employee apna check-out kare"""
    notes = serializers.CharField(required=False, allow_blank=True)


# ─── LEAVE ───────────────────────────────────────────────────

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        exclude = ("tenant",)
        read_only_fields = ("id",)


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_detail = LeaveTypeSerializer(source="leave_type", read_only=True)
    remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeaveBalance
        exclude = ("tenant",)
        read_only_fields = ("id", "remaining")


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_detail = MiniUserSerializer(source="employee", read_only=True)
    leave_type_detail = LeaveTypeSerializer(source="leave_type", read_only=True)
    reviewed_by_detail = MiniUserSerializer(source="reviewed_by", read_only=True)

    class Meta:
        model = LeaveRequest
        exclude = ("tenant",)
        read_only_fields = (
            "id", "total_days", "status",
            "reviewed_by", "reviewed_at",
            "rejection_reason", "created_at", "updated_at"
        )

    def validate(self, data):
        from_date = data.get("from_date")
        to_date = data.get("to_date")
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError("to_date cannot be before from_date.")
        return data


class LeaveApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approved", "rejected"])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["action"] == "rejected" and not data.get("rejection_reason"):
            raise serializers.ValidationError("rejection_reason required when rejecting.")
        return data


# ─── PAYROLL ─────────────────────────────────────────────────

class SalaryStructureSerializer(serializers.ModelSerializer):
    employee_detail = MiniUserSerializer(source="employee", read_only=True)
    gross_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_deductions = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    net_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = SalaryStructure
        exclude = ("tenant",)
        read_only_fields = ("id", "created_at", "updated_at")


class PaySlipSerializer(serializers.ModelSerializer):
    employee_detail = MiniUserSerializer(source="employee", read_only=True)

    class Meta:
        model = PaySlip
        exclude = ("tenant",)
        read_only_fields = ("id",)


class PayrollRunSerializer(serializers.ModelSerializer):
    slips = PaySlipSerializer(many=True, read_only=True)
    generated_by_detail = MiniUserSerializer(source="generated_by", read_only=True)
    total_employees = serializers.SerializerMethodField()
    total_net = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        exclude = ("tenant",)
        read_only_fields = ("id", "generated_by", "created_at", "updated_at")

    def get_total_employees(self, obj):
        return obj.slips.count()

    def get_total_net(self, obj):
        return sum(s.net_salary for s in obj.slips.all())
