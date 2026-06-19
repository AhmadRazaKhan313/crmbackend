from rest_framework import serializers
from .models import Client, SalesDetail, TechDetail, SEODetail, Payment, ClientFile


class SalesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesDetail
        exclude = ("client",)


class TechDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechDetail
        exclude = ("client",)


class SEODetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SEODetail
        exclude = ("client",)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        exclude = ("tenant", "client")
        read_only_fields = ("paid_at", "created_at")


class ClientFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = ClientFile
        fields = ("id", "file", "name", "uploaded_by_name", "uploaded_at")
        read_only_fields = ("uploaded_at",)


class ClientListSerializer(serializers.ModelSerializer):
    assigned_to_name  = serializers.CharField(source="assigned_to.full_name",  read_only=True)
    created_by_name   = serializers.CharField(source="created_by.full_name",   read_only=True)
    converted_from_id = serializers.IntegerField(source="converted_from.id",   read_only=True)

    class Meta:
        model  = Client
        fields = (
            "id", "full_name", "email", "phone", "country", "company",
            "department", "status", "tag",
            "assigned_to", "assigned_to_name",
            "converted_from_id",
            "created_by_name",
            "is_archived", "created_at", "updated_at",
        )


class ClientDetailSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)
    created_by_name  = serializers.CharField(source="created_by.full_name",  read_only=True)

    # Department-specific details — null agar exist nahi karta
    sales_detail = SalesDetailSerializer(read_only=True)
    tech_detail  = TechDetailSerializer(read_only=True)
    seo_detail   = SEODetailSerializer(read_only=True)

    # Related data
    payments = PaymentSerializer(many=True, read_only=True)
    files    = ClientFileSerializer(many=True, read_only=True)

    # Converted from lead
    converted_from_name = serializers.SerializerMethodField()

    class Meta:
        model  = Client
        fields = (
            "id", "full_name", "email", "phone", "country", "company",
            "department", "status", "tag",
            "assigned_to", "assigned_to_name",
            "converted_from", "converted_from_name",
            "created_by_name",
            "notes",
            "sales_detail", "tech_detail", "seo_detail",
            "payments", "files",
            "is_archived", "created_at", "updated_at",
        )

    def get_converted_from_name(self, obj):
        if obj.converted_from:
            return obj.converted_from.full_name
        return None


class ClientCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Client
        exclude = ("tenant", "created_by", "is_archived", "converted_from")

    def create(self, validated_data):
        request = self.context["request"]
        if not validated_data.get("department") and request.user.department:
            validated_data["department"] = request.user.department
        return Client.objects.create(
            tenant     = request.user.tenant,
            created_by = request.user,
            **validated_data
        )