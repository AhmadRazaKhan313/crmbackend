from .permissions import same_tenant, same_department


class TenantQuerysetMixin:
    """
    View mixin — automatically tenant filter karta hai queryset pe.
    Super admin ko sab milta hai.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_super_admin:
            return qs
        return qs.filter(tenant=user.tenant)


class DepartmentQuerysetMixin(TenantQuerysetMixin):
    """
    Tenant filter ke baad department filter bhi karta hai.
    CEO/COO ko poora tenant milta hai.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role in ("ceo", "coo", "sales_director"):
            return qs
        if user.department:
            return qs.filter(department=user.department)
        return qs.none()