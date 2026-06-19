from rest_framework import serializers
from .models import Invoice, Expense


class InvoiceSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.CharField(source="issued_by.full_name", read_only=True)
    balance_due    = serializers.ReadOnlyField()

    class Meta:
        model  = Invoice
        exclude = ("tenant",)
        read_only_fields = ("invoice_no", "issued_by", "paid_at", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context["request"]
        if validated_data.get("client") and not validated_data.get("client_name"):
            validated_data["client_name"] = validated_data["client"].full_name
        return Invoice.objects.create(
            tenant=request.user.tenant,
            issued_by=request.user,
            **validated_data
        )


class ExpenseSerializer(serializers.ModelSerializer):
    paid_by_name = serializers.CharField(source="paid_by.full_name", read_only=True)

    class Meta:
        model  = Expense
        exclude = ("tenant",)
        read_only_fields = ("paid_by", "created_at")

    def create(self, validated_data):
        request = self.context["request"]
        return Expense.objects.create(
            tenant=request.user.tenant,
            paid_by=request.user,
            **validated_data
        )
