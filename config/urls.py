from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/",             admin.site.urls),
    path("api/auth/",          include("authentication.urls")),
    path("api/tenant/",        include("tenants.urls")),
    path("api/core/",          include("core.urls")),
    path("api/leads/",         include("leads.urls")),
    path("api/clients/",       include("clients.urls")),
    path("api/tasks/",         include("tasks.urls")),
    path("api/reports/",       include("reports.urls")),
    path("api/departments/",   include("departments.urls")),
    path("api/analytics/",     include("analytics.urls")),
    path("api/hrms/",          include("hrms.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/finance/",       include("finance.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
