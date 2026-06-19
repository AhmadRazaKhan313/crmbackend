from django.contrib import admin
from .models import (
    Shift, EmployeeShift, Attendance,
    LeaveType, LeaveRequest, LeaveBalance,
    SalaryStructure, PayrollRun, PaySlip
)

admin.site.register(Shift)
admin.site.register(EmployeeShift)
admin.site.register(Attendance)
admin.site.register(LeaveType)
admin.site.register(LeaveRequest)
admin.site.register(LeaveBalance)
admin.site.register(SalaryStructure)
admin.site.register(PayrollRun)
admin.site.register(PaySlip)
