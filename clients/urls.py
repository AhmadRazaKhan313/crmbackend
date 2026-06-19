from django.urls import path
from . import views

urlpatterns = [
    # List / Create
    path("", views.ClientListCreateView.as_view()),

    # Detail / Edit / Delete
    path("<int:pk>/", views.ClientDetailView.as_view()),

    # ✅ Department-specific details
    path("<int:pk>/sales-detail/", views.ClientSalesDetailView.as_view()),
    path("<int:pk>/tech-detail/",  views.ClientTechDetailView.as_view()),
    path("<int:pk>/seo-detail/",   views.ClientSEODetailView.as_view()),

    # Payments
    path("<int:pk>/payments/",     views.ClientPaymentView.as_view()),

    # Files
    path("<int:pk>/files/",        views.ClientFileView.as_view()),
]