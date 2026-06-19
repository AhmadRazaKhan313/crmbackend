from django.urls import path
from . import views

urlpatterns = [
    path("",               views.NotificationListView.as_view()),
    path("unread-count/",  views.NotificationUnreadCountView.as_view()),
    path("read-all/",      views.NotificationMarkAllReadView.as_view()),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view()),
    path("<int:pk>/",      views.NotificationDeleteView.as_view()),
]
