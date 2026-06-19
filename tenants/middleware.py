from django.http import JsonResponse
from .models import Tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host  = request.get_host().split(":")[0]
        parts = host.split(".")

        slug = request.headers.get("X-Tenant-Slug") or (
            parts[0] if len(parts) > 2 else None
        )

        if slug and slug not in ("www", "api", "admin"):
            try:
                tenant = Tenant.objects.select_related("features").get(
                    slug=slug, status__in=("active", "trial")
                )
                if not self._is_access_allowed(tenant):
                    return JsonResponse(
                        {"detail": "Trial expired. Please upgrade your plan."},
                        status=402
                    )
                request.tenant = tenant
            except Tenant.DoesNotExist:
                return JsonResponse({"detail": "Invalid tenant."}, status=404)
        else:
            request.tenant = None

        return self.get_response(request)

    def _is_access_allowed(self, tenant):
        from django.utils import timezone
        if tenant.status in ("suspended", "cancelled"):
            return False
        if tenant.status == "trial" and tenant.trial_ends_at:
            if timezone.now() > tenant.trial_ends_at:
                tenant.status = "suspended"
                tenant.save(update_fields=["status"])
                return False
        return True
