"""
Demo Users Setup Script
Run: python manage.py shell < create_demo_users.py
"""
from authentication.models import User
from tenants.models import Tenant, TenantFeature

# ── 1. Tenant create karo ────────────────────────────────
tenant, _ = Tenant.objects.get_or_create(
    slug="demo-company",
    defaults={
        "name":   "Demo Company",
        "email":  "demo@company.com",
        "status": "active",
        "plan":   "pro",
    }
)

# Feature flags — sab ON
features, _ = TenantFeature.objects.get_or_create(tenant=tenant)
features.leads_module       = True
features.clients_module     = True
features.tasks_module       = True
features.reports_module     = True
features.departments_module = True
features.analytics          = True
features.hrms               = True
features.save()

print(f"Tenant: {tenant.name} ✓")

# ── 2. Super Admin ───────────────────────────────────────
if not User.objects.filter(email="superadmin@crm.com").exists():
    superadmin = User.objects.create_superuser(
        email    = "superadmin@crm.com",
        password = "Admin@1234",
        full_name= "Super Admin",
    )
    superadmin.is_super_admin = True
    superadmin.save()
    print("Super Admin created ✓")
else:
    print("Super Admin already exists ✓")

# ── 3. Demo Users ────────────────────────────────────────
demo_users = [
    {"email": "ceo@demo.com",            "password": "Demo@1234", "full_name": "Ahmed Khan",     "role": "ceo",            "department": "sales"},
    {"email": "coo@demo.com",            "password": "Demo@1234", "full_name": "Sara Ali",       "role": "coo",            "department": "tech"},
    {"email": "depthead@demo.com",       "password": "Demo@1234", "full_name": "Usman Malik",    "role": "dept_head",      "department": "sales"},
    {"email": "salesdirector@demo.com",  "password": "Demo@1234", "full_name": "Fatima Raza",    "role": "sales_director", "department": "sales"},
    {"email": "leadmanager@demo.com",    "password": "Demo@1234", "full_name": "Bilal Ahmed",    "role": "lead_manager",   "department": "sales"},
    {"email": "salesmanager@demo.com",   "password": "Demo@1234", "full_name": "Hina Shah",      "role": "sales_manager",  "department": "sales"},
    {"email": "employee1@demo.com",      "password": "Demo@1234", "full_name": "Ali Hassan",     "role": "lead_employee",  "department": "sales"},
    {"email": "employee2@demo.com",      "password": "Demo@1234", "full_name": "Zara Hussain",   "role": "sales_employee", "department": "tech"},
]

for u in demo_users:
    if not User.objects.filter(email=u["email"]).exists():
        user = User.objects.create_user(
            email     = u["email"],
            password  = u["password"],
            full_name = u["full_name"],
        )
        user.role       = u["role"]
        user.department = u["department"]
        user.tenant     = tenant
        user.is_active  = True
        user.save()
        print(f"{u['role']:20} → {u['email']} created ✓")
    else:
        print(f"{u['role']:20} → {u['email']} already exists ✓")

print("\nAll demo users ready!")
print("="*50)
