from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.HRMSDashboardView.as_view()),

    # Shifts
    path("shifts/", views.ShiftListCreateView.as_view()),
    path("shifts/<int:pk>/", views.ShiftDetailView.as_view()),
    path("shifts/assign/", views.AssignShiftView.as_view()),

    # Attendance
    path("attendance/", views.AttendanceListView.as_view()),
    path("attendance/today/", views.TodayAttendanceView.as_view()),
    path("attendance/check-in/", views.MyAttendanceCheckInView.as_view()),
    path("attendance/check-out/", views.MyAttendanceCheckOutView.as_view()),

    # Leave Types
    path("leave-types/", views.LeaveTypeListView.as_view()),

    # Leave Requests
    path("leaves/", views.LeaveRequestListCreateView.as_view()),
    path("leaves/<int:pk>/", views.LeaveRequestDetailView.as_view()),
    path("leaves/<int:pk>/approve/", views.LeaveApprovalView.as_view()),

    # Leave Balance
    path("leave-balance/", views.LeaveBalanceView.as_view()),

    # Salary
    path("salary/", views.SalaryStructureView.as_view()),
    path("salary/<int:emp_id>/", views.EmployeeSalaryView.as_view()),

    # Payroll
    path("payroll/", views.PayrollRunListView.as_view()),
    path("payroll/<int:pk>/", views.PayrollRunDetailView.as_view()),
    path("payroll/my-slips/", views.MyPaySlipsView.as_view()),
]
