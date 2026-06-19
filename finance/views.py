from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Invoice, Expense
from .serializers import InvoiceSerializer, ExpenseSerializer
from core.permissions import IsManagerOrAbove, IsCEOOrAbove

INVOICE_PATCH_ALLOWED = {
    "client", "client_name", "client_email",
    "amount", "paid_amount", "currency",
    "items", "status", "due_date", "notes",
}
EXPENSE_PATCH_ALLOWED = {
    "title", "amount", "currency", "category",
    "department", "date", "notes", "receipt",
}


class FinanceOverviewView(APIView):
    permission_classes = (IsCEOOrAbove,)

    def get(self, request):
        tenant   = request.user.tenant
        invoices = Invoice.objects.filter(tenant=tenant)
        expenses = Expense.objects.filter(tenant=tenant)
        month    = request.query_params.get("month")
        if month:
            try:
                year, m = month.split("-")
                invoices = invoices.filter(created_at__year=year, created_at__month=m)
                expenses = expenses.filter(date__year=year, date__month=m)
            except (ValueError, AttributeError):
                pass
        total_invoiced = invoices.aggregate(t=Sum("amount"))["t"] or Decimal("0")
        total_paid     = invoices.aggregate(t=Sum("paid_amount"))["t"] or Decimal("0")
        total_expenses = expenses.aggregate(t=Sum("amount"))["t"] or Decimal("0")
        overdue_qs     = invoices.filter(status="overdue")
        total_overdue  = overdue_qs.aggregate(t=Sum("amount"))["t"] or Decimal("0")
        return Response({
            "total_invoiced": total_invoiced,
            "total_paid":     total_paid,
            "total_overdue":  total_overdue,
            "total_expenses": total_expenses,
            "net_revenue":    total_paid - total_expenses,
            "invoice_count":  invoices.count(),
            "expense_count":  expenses.count(),
            "overdue_count":  overdue_qs.count(),
        })


class InvoiceListCreateView(APIView):
    permission_classes = (IsManagerOrAbove,)

    def get(self, request):
        qs = Invoice.objects.filter(tenant=request.user.tenant)
        if request.query_params.get("status"): qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("search"):
            s = request.query_params["search"]
            qs = qs.filter(Q(client_name__icontains=s) | Q(invoice_no__icontains=s))
        return Response(InvoiceSerializer(qs, many=True).data)

    def post(self, request):
        serializer = InvoiceSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(InvoiceSerializer(serializer.save()).data, status=status.HTTP_201_CREATED)


class InvoiceDetailView(APIView):
    permission_classes = (IsManagerOrAbove,)

    def _get(self, pk, tenant):
        return get_object_or_404(Invoice, pk=pk, tenant=tenant)

    def get(self, request, pk):
        return Response(InvoiceSerializer(self._get(pk, request.user.tenant)).data)

    def patch(self, request, pk):
        invoice    = self._get(pk, request.user.tenant)
        safe_data  = {k: v for k, v in request.data.items() if k in INVOICE_PATCH_ALLOWED}
        serializer = InvoiceSerializer(invoice, data=safe_data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        if safe_data.get("status") == "paid" and not invoice.paid_at:
            invoice.paid_at = timezone.now()
            invoice.save()
        return Response(InvoiceSerializer(invoice).data)

    def delete(self, request, pk):
        invoice = self._get(pk, request.user.tenant)
        if invoice.status == "paid":
            return Response({"detail": "Paid invoices cannot be deleted."}, status=status.HTTP_400_BAD_REQUEST)
        invoice.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExpenseListCreateView(APIView):
    permission_classes = (IsManagerOrAbove,)

    def get(self, request):
        qs = Expense.objects.filter(tenant=request.user.tenant)
        if request.query_params.get("category"): qs = qs.filter(category=request.query_params["category"])
        if request.query_params.get("department"): qs = qs.filter(department=request.query_params["department"])
        if request.query_params.get("month"):
            try:
                year, m = request.query_params["month"].split("-")
                qs = qs.filter(date__year=year, date__month=m)
            except (ValueError, AttributeError):
                pass
        return Response(ExpenseSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(ExpenseSerializer(serializer.save()).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(APIView):
    permission_classes = (IsManagerOrAbove,)

    def _get(self, pk, tenant):
        return get_object_or_404(Expense, pk=pk, tenant=tenant)

    def get(self, request, pk):
        return Response(ExpenseSerializer(self._get(pk, request.user.tenant)).data)

    def patch(self, request, pk):
        expense    = self._get(pk, request.user.tenant)
        safe_data  = {k: v for k, v in request.data.items() if k in EXPENSE_PATCH_ALLOWED}
        serializer = ExpenseSerializer(expense, data=safe_data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(ExpenseSerializer(serializer.save()).data)

    def delete(self, request, pk):
        self._get(pk, request.user.tenant).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
