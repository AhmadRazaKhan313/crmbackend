from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.OverviewAnalyticsView.as_view()),
    path("kpi/", views.KPIView.as_view()),
]