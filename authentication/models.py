from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class DEPARTMENTS(models.TextChoices):
    SALES = "sales", "Sales"
    TECH = "tech", "Tech"
    SEO = "seo", "SEO"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_super_admin", True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class ROLES(models.TextChoices):
        CEO = "ceo", "CEO"
        COO = "coo", "COO"
        DEPT_HEAD = "dept_head", "Department Head"
        SALES_DIRECTOR = "sales_director", "Sales Director"
        LEAD_MANAGER = "lead_manager", "Lead Manager"
        SALES_MANAGER = "sales_manager", "Sales Manager"
        LEAD_EMPLOYEE = "lead_employee", "Lead Employee"
        SALES_EMPLOYEE = "sales_employee", "Sales Employee"

    class DEPARTMENTS(models.TextChoices):
        SALES = "sales", "Sales"
        TECH = "tech", "Tech"
        SEO = "seo", "SEO"

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=ROLES.choices)
    department = models.CharField(max_length=20, choices=DEPARTMENTS.choices, blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users"
    )
    is_super_admin = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_top_level(self):
        return self.role in (self.ROLES.CEO, self.ROLES.COO)

    @property
    def dept_code(self):
        codes = {"sales": "SALE", "tech": "TEC", "seo": "SEO"}
        return codes.get(self.department, "GEN")

    def save(self, *args, **kwargs):
        if not self.employee_id and self.role and self.pk is None:
            super().save(*args, **kwargs)
            self.employee_id = f"{self.dept_code}-{self.get_role_display()[:3].upper()}-{str(self.pk).zfill(3)}"
            kwargs["force_insert"] = False
        super().save(*args, **kwargs)