from django.urls import path
from . import views

urlpatterns = [
    path("", views.DepartmentListCreateView.as_view()),
    path("<int:pk>/", views.DepartmentDetailView.as_view()),
]