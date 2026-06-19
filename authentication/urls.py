from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views_employees import (
    EmployeeListCreateView,
    EmployeeDetailView,
    EmployeeRoleAssignView,
    AdminPasswordResetView,
)

urlpatterns = [
    path("login/",           views.LoginView.as_view()),
    path("register/",        views.RegisterView.as_view()),
    path("logout/",          views.LogoutView.as_view()),
    path("me/",              views.MeView.as_view()),
    path("change-password/", views.ChangePasswordView.as_view()),
    path("token/refresh/",   TokenRefreshView.as_view()),

    path("employees/",                         EmployeeListCreateView.as_view()),
    path("employees/<int:pk>/",                EmployeeDetailView.as_view()),
    path("employees/<int:pk>/roles/",          EmployeeRoleAssignView.as_view()),
    path("employees/<int:pk>/reset-password/", AdminPasswordResetView.as_view()), 
]