from django.urls import path
from . import views

urlpatterns = [
    # Public
    path("register/", views.TenantRegisterView.as_view()),

    # Authenticated tenant
    path("me/", views.TenantDetailView.as_view()),

    # Super Admin — tenant management
    path("admin/stats/", views.SuperAdminStatsView.as_view()),
    path("admin/tenants/", views.SuperAdminTenantListView.as_view()),
    path("admin/tenants/<int:tenant_id>/", views.SuperAdminTenantDetailView.as_view()),
    path("admin/tenants/<int:tenant_id>/features/", views.SuperAdminFeatureFlagView.as_view()),
]
