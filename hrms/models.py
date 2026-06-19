from django.db import models
from django.utils import timezone
from tenants.mixins import TenantModel


# ─────────────────────────────────────────────────────────────
# SHIFT
# ─────────────────────────────────────────────────────────────

class Shift(TenantModel):
    """Working shift definition — e.g. Morning 9am-5pm"""
    name = models.CharField(max_length=60)           # e.g. "Morning Shift"
    start_time = models.TimeField()                  # 09:00
    end_time = models.TimeField()                    # 17:00
    working_days = models.JSONField(default=list)    # ["Mon","Tue","Wed","Thu","Fri"]
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hrms_shifts"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time}–{self.end_time})"


class EmployeeShift(TenantModel):
    """Employee ko kaunsa shift assign hai"""
    employee = models.OneToOneField(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="shift_assignment"
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        related_name="employees"
    )
    effective_from = models.DateField(default=timezone.now)
    assigned_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="shift_assignments_given"
    )

    class Meta:
        db_table = "hrms_employee_shifts"

    def __str__(self):
        return f"{self.employee.full_name} → {self.shift}"


# ─────────────────────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────────────────────

class Attendance(TenantModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        HALF_DAY = "half_day", "Half Day"
        LATE = "late", "Late"
        ON_LEAVE = "on_leave", "On Leave"
        HOLIDAY = "holiday", "Holiday"

    employee = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="attendances"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)

    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)

    # Auto-calculated working hours (minutes)
    working_minutes = models.PositiveIntegerField(default=0)

    # Late / overtime (minutes)
    late_minutes = models.PositiveIntegerField(default=0)
    overtime_minutes = models.PositiveIntegerField(default=0)

    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="attendance_marked"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hrms_attendance"
        ordering = ["-date"]
        unique_together = ("employee", "date")

    def __str__(self):
        return f"{self.employee.full_name} — {self.date} [{self.status}]"

    def save(self, *args, **kwargs):
        # Auto-calculate working_minutes
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.working_minutes = max(int(delta.total_seconds() / 60), 0)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# LEAVE
# ─────────────────────────────────────────────────────────────

class LeaveType(TenantModel):
    """Tenant define kar sakta hai apne leave types"""
    name = models.CharField(max_length=60)           # "Annual Leave", "Sick Leave"
    max_days_per_year = models.PositiveIntegerField(default=15)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=10, default="#6366f1")  # for UI badge

    class Meta:
        db_table = "hrms_leave_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveRequest(TenantModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    employee = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="requests"
    )

    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.PositiveIntegerField(default=1)

    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Approval
    reviewed_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="leave_reviews"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hrms_leave_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.leave_type} ({self.from_date} to {self.to_date})"

    def save(self, *args, **kwargs):
        # Auto-calculate total_days
        if self.from_date and self.to_date:
            delta = self.to_date - self.from_date
            self.total_days = max(delta.days + 1, 1)
        super().save(*args, **kwargs)


class LeaveBalance(TenantModel):
    """Per employee per leave type remaining balance"""
    employee = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="leave_balances"
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name="balances"
    )
    year = models.PositiveIntegerField()
    allocated = models.PositiveIntegerField(default=0)
    used = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "hrms_leave_balances"
        unique_together = ("employee", "leave_type", "year")

    @property
    def remaining(self):
        return max(self.allocated - self.used, 0)

    def __str__(self):
        return f"{self.employee.full_name} — {self.leave_type} {self.year} ({self.remaining} left)"


# ─────────────────────────────────────────────────────────────
# PAYROLL
# ─────────────────────────────────────────────────────────────

class SalaryStructure(TenantModel):
    """Employee ki salary breakdown"""
    employee = models.OneToOneField(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="salary_structure"
    )
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    house_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    effective_from = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hrms_salary_structures"

    @property
    def gross_salary(self):
        return (
            self.basic_salary + self.house_allowance +
            self.transport_allowance + self.medical_allowance +
            self.other_allowances
        )

    @property
    def total_deductions(self):
        return self.tax_deduction + self.provident_fund + self.other_deductions

    @property
    def net_salary(self):
        return self.gross_salary - self.total_deductions

    def __str__(self):
        return f"{self.employee.full_name} — Net: {self.net_salary}"


class PayrollRun(TenantModel):
    """Monthly payroll generation"""
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROCESSED = "processed", "Processed"
        PAID = "paid", "Paid"

    month = models.PositiveIntegerField()   # 1-12
    year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    generated_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="payroll_runs"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "hrms_payroll_runs"
        unique_together = ("tenant", "month", "year")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"Payroll {self.month}/{self.year} [{self.status}]"


class PaySlip(TenantModel):
    """Per employee payslip for a payroll run"""
    payroll_run = models.ForeignKey(PayrollRun, on_delete=models.CASCADE, related_name="slips")
    employee = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="payslips"
    )

    # Snapshot of salary at time of payroll
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Deductions
    tax_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    provident_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Attendance adjustments
    days_present = models.PositiveIntegerField(default=0)
    days_absent = models.PositiveIntegerField(default=0)
    leave_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overtime_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)

    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "hrms_payslips"
        unique_together = ("payroll_run", "employee")
        ordering = ["employee__full_name"]

    def __str__(self):
        return f"{self.employee.full_name} — {self.payroll_run}"
