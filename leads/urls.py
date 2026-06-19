from django.urls import path
from . import views

urlpatterns = [
    path("",                   views.LeadListCreateView.as_view()),

    path("bulk-upload/",       views.LeadBulkUploadView.as_view()),
    path("export/",            views.LeadExportView.as_view()),
    path("template/",          views.LeadTemplateDownloadView.as_view()),

    path("<int:pk>/",          views.LeadDetailView.as_view()),
    path("<int:pk>/assign/",   views.LeadAssignView.as_view()),
    path("<int:pk>/activity/", views.LeadActivityView.as_view()),
    path("<int:pk>/convert/", views.LeadConvertView.as_view()),
]