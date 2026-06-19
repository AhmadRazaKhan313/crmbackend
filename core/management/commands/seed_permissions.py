from django.core.management.base import BaseCommand
from core.models import Permission

PERMISSIONS = [
    ("leads",         "view",   "leads.view",           "View Leads"),
    ("leads",         "create", "leads.create",         "Create Leads"),
    ("leads",         "edit",   "leads.edit",           "Edit Leads"),
    ("leads",         "delete", "leads.delete",         "Delete Leads"),
    ("leads",         "export", "leads.export",         "Export Leads"),
    ("leads",         "assign", "leads.assign",         "Assign Leads"),
    ("clients",       "view",   "clients.view",         "View Clients"),
    ("clients",       "create", "clients.create",       "Create Clients"),
    ("clients",       "edit",   "clients.edit",         "Edit Clients"),
    ("clients",       "delete", "clients.delete",       "Delete Clients"),
    ("clients",       "export", "clients.export",       "Export Clients"),
    ("clients",       "assign", "clients.assign",       "Assign Clients"),
    ("tasks",         "view",   "tasks.view",           "View Tasks"),
    ("tasks",         "create", "tasks.create",         "Create Tasks"),
    ("tasks",         "edit",   "tasks.edit",           "Edit Tasks"),
    ("tasks",         "delete", "tasks.delete",         "Delete Tasks"),
    ("tasks",         "assign", "tasks.assign",         "Assign Tasks"),
    ("reports",       "view",   "reports.view",         "View Reports"),
    ("reports",       "create", "reports.create",       "Submit Reports"),
    ("reports",       "approve","reports.approve",      "Approve Reports"),
    ("finance",       "view",   "finance.view",         "View Finance"),
    ("finance",       "create", "finance.create",       "Create Invoices"),
    ("finance",       "edit",   "finance.edit",         "Edit Invoices"),
    ("finance",       "delete", "finance.delete",       "Delete Invoices"),
    ("finance",       "export", "finance.export",       "Export Finance"),
    ("employees",     "view",   "employees.view",       "View Employees"),
    ("employees",     "create", "employees.create",     "Add Employees"),
    ("employees",     "edit",   "employees.edit",       "Edit Employees"),
    ("employees",     "delete", "employees.delete",     "Deactivate Employees"),
    ("departments",   "view",   "departments.view",     "View Departments"),
    ("departments",   "create", "departments.create",   "Create Departments"),
    ("departments",   "edit",   "departments.edit",     "Edit Departments"),
    ("departments",   "delete", "departments.delete",   "Deactivate Departments"),
    ("analytics",     "view",   "analytics.view",       "View Analytics"),
    ("notifications", "view",   "notifications.view",   "View Notifications"),
    ("settings",      "view",   "settings.view",        "View Settings"),
    ("settings",      "edit",   "settings.edit",        "Edit Settings"),
    ("delivery",      "view",   "delivery.view",        "View Delivery"),
    ("delivery",      "create", "delivery.create",      "Create Deliveries"),
    ("delivery",      "edit",   "delivery.edit",        "Edit Deliveries"),
]


class Command(BaseCommand):
    help = "Seed all system permissions into the database"

    def handle(self, *args, **kwargs):
        created = 0
        skipped = 0
        for module, action, codename, label in PERMISSIONS:
            _, was_created = Permission.objects.get_or_create(
                codename=codename,
                defaults={"module": module, "action": action, "label": label}
            )
            if was_created:
                created += 1
            else:
                skipped += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Done — {created} created, {skipped} already existed."
            )
        )
