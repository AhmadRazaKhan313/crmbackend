from django.urls import path
from . import views

urlpatterns = [
    path("", views.TaskListCreateView.as_view()),
    path("<int:pk>/", views.TaskDetailView.as_view()),
    path("<int:pk>/comment/", views.TaskCommentView.as_view()),
]