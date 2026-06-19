from django.urls import path
from . import views

urlpatterns = [
    path("overview/",          views.FinanceOverviewView.as_view()),
    path("invoices/",          views.InvoiceListCreateView.as_view()),
    path("invoices/<int:pk>/", views.InvoiceDetailView.as_view()),
    path("expenses/",          views.ExpenseListCreateView.as_view()),
    path("expenses/<int:pk>/", views.ExpenseDetailView.as_view()),
]
