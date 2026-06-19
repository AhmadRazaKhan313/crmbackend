from django.urls import path
from . import views

urlpatterns = [
    path("permissions/",              views.PermissionListView.as_view()),
    path("roles/",                    views.RoleListCreateView.as_view()),
    path("roles/assign/",             views.AssignRoleView.as_view()),
    path("roles/user/<int:user_id>/", views.UserRolesView.as_view()),
    path("roles/<int:pk>/",           views.RoleDetailView.as_view()),
]
