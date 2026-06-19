from rest_framework import serializers
from .models import Lead, LeadActivity


class LeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model  = LeadActivity
        fields = ("id", "activity_type", "note", "created_by_name", "created_at")


class LeadListSerializer(serializers.ModelSerializer):
    assigned_to_name       = serializers.CharField(source="assigned_to.full_name",  read_only=True)
    assigned_to_employee_id = serializers.CharField(source="assigned_to.employee_id", read_only=True)
    created_by_name        = serializers.CharField(source="created_by.full_name",   read_only=True)
    staff_name             = serializers.ReadOnlyField()
    staff_id               = serializers.ReadOnlyField()

    class Meta:
        model  = Lead
        fields = (
            "id", "serial_no", "full_name", "email", "phone",
            "contact_no", "country", "company",
            "source", "platform_link",
            "instagram_url", "facebook_url", "linkedin_url",
            "lead_insta_id", "lead_fb_id", "lead_linkedin_id", "lead_whatsapp_no",
            "assigned_to", "assigned_to_name", "assigned_to_employee_id",
            "staff_name", "staff_id",
            "staff_insta_id", "staff_fb_id", "staff_linkedin_id", "staff_whatsapp_id",
            "department", "status", "service_interest",
            "created_by_name", "is_archived", "created_at", "updated_at",
        )


class LeadDetailSerializer(serializers.ModelSerializer):
    activities             = LeadActivitySerializer(many=True, read_only=True)
    assigned_to_name       = serializers.CharField(source="assigned_to.full_name",  read_only=True)
    assigned_to_employee_id = serializers.CharField(source="assigned_to.employee_id", read_only=True)
    created_by_name        = serializers.CharField(source="created_by.full_name",   read_only=True)
    staff_name             = serializers.ReadOnlyField()
    staff_id               = serializers.ReadOnlyField()

    class Meta:
        model  = Lead
        fields = (
            "id", "serial_no", "full_name", "email", "phone",
            "contact_no", "country", "company",
            "source", "platform_link",
            "instagram_url", "facebook_url", "linkedin_url",
            "lead_insta_id", "lead_fb_id", "lead_linkedin_id", "lead_whatsapp_no",
            "assigned_to", "assigned_to_name", "assigned_to_employee_id",
            "staff_name", "staff_id",
            "staff_insta_id", "staff_fb_id", "staff_linkedin_id", "staff_whatsapp_id",
            "department", "status", "service_interest",
            "notes", "questionnaire",
            "created_by", "created_by_name",
            "is_archived", "created_at", "updated_at",
            "activities",
        )


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model   = Lead
        exclude = ("tenant", "created_by", "is_archived")

    def validate_serial_no(self, value):
        request = self.context["request"]
        qs = Lead.objects.filter(tenant=request.user.tenant, serial_no=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("This serial number is already in use.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        if not validated_data.get("department") and request.user.department:
            validated_data["department"] = request.user.department
        return Lead.objects.create(
            tenant     = request.user.tenant,
            created_by = request.user,
            **validated_data
        )