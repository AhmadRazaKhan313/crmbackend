from rest_framework import serializers
from .models import Tenant, TenantFeature


class TenantFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantFeature
        exclude = ("id", "tenant")


class TenantSerializer(serializers.ModelSerializer):
    features = TenantFeatureSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = (
            "id", "name", "slug", "email", "phone",
            "logo", "plan", "status", "trial_ends_at",
            "created_at", "features"
        )
        read_only_fields = ("id", "slug", "created_at")


class TenantRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ("name", "email", "phone")

    def create(self, validated_data):
        from django.utils.text import slugify
        name = validated_data["name"]
        base_slug = slugify(name)
        slug = base_slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        tenant = Tenant.objects.create(slug=slug, **validated_data)
        TenantFeature.objects.create(tenant=tenant)
        return tenant
