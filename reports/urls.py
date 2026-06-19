from django.urls import path
from . import views

urlpatterns = [
    path("", views.DailyReportListCreateView.as_view()),
    path("<int:pk>/", views.DailyReportDetailView.as_view()),
    path("<int:pk>/review/", views.ReportReviewView.as_view()),
]