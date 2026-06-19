from django.db import models
from tenants.mixins import TenantModel


class Lead(TenantModel):
    class Status(models.TextChoices):
        NEW        = "new",       "New"
        CONTACTED  = "contacted", "Contacted"
        INTERESTED = "interested","Interested"
        FOLLOW_UP  = "follow_up", "Follow Up"
        CONVERTED  = "converted", "Converted"
        REJECTED   = "rejected",  "Rejected"

    class Source(models.TextChoices):
        INSTAGRAM = "instagram", "Instagram"
        FACEBOOK  = "facebook",  "Facebook"
        LINKEDIN  = "linkedin",  "LinkedIn"
        WHATSAPP  = "whatsapp",  "WhatsApp"
        WEBSITE   = "website",   "Website"
        EMAIL     = "email",     "Email"
        OTHER     = "other",     "Other"

    class Department(models.TextChoices):
        SALES = "sales", "Sales"
        TECH  = "tech",  "Tech"
        SEO   = "seo",   "SEO"

    serial_no        = models.CharField(max_length=20, blank=True, unique=False)
    full_name        = models.CharField(max_length=120)
    email            = models.EmailField(blank=True)
    phone            = models.CharField(max_length=20, blank=True)
    country          = models.CharField(max_length=60, blank=True)
    company          = models.CharField(max_length=120, blank=True)
    source           = models.CharField(max_length=20, choices=Source.choices)
    department       = models.CharField(max_length=20, choices=Department.choices)
    status           = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    service_interest = models.CharField(max_length=120, blank=True)
    notes            = models.TextField(blank=True)
    questionnaire    = models.TextField(blank=True)
    platform_link    = models.URLField(blank=True)
    contact_no       = models.CharField(max_length=20, blank=True)
    lead_insta_id    = models.CharField(max_length=100, blank=True)
    lead_fb_id       = models.CharField(max_length=100, blank=True)
    lead_linkedin_id = models.CharField(max_length=100, blank=True)
    lead_whatsapp_no = models.CharField(max_length=20,  blank=True)
    assigned_to      = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_leads")
    created_by       = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True, related_name="created_leads")
    staff_insta_id    = models.CharField(max_length=100, blank=True)
    staff_fb_id       = models.CharField(max_length=100, blank=True)
    staff_linkedin_id = models.CharField(max_length=100, blank=True)
    staff_whatsapp_id = models.CharField(max_length=20,  blank=True)
    instagram_url    = models.URLField(blank=True)
    facebook_url     = models.URLField(blank=True)
    linkedin_url     = models.URLField(blank=True)
    is_archived      = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.serial_no:
            from django.db import transaction
            with transaction.atomic():
                last = (
                    Lead.objects.select_for_update()
                    .filter(tenant=self.tenant)
                    .exclude(serial_no="")
                    .order_by("-serial_no")
                    .first()
                )
                if last and last.serial_no.isdigit():
                    next_num = int(last.serial_no) + 1
                else:
                    next_num = 1
                self.serial_no = str(next_num).zfill(3)
        super().save(*args, **kwargs)

    @property
    def staff_name(self):
        return self.assigned_to.full_name if self.assigned_to else ""

    @property
    def staff_id(self):
        return getattr(self.assigned_to, "employee_id", "") or "" if self.assigned_to else ""


class LeadActivity(models.Model):
    class ActivityType(models.TextChoices):
        NOTE          = "note",          "Note"
        CALL          = "call",          "Call"
        EMAIL         = "email",         "Email"
        WHATSAPP      = "whatsapp",      "WhatsApp"
        MEETING       = "meeting",       "Meeting"
        STATUS_CHANGE = "status_change", "Status Change"

    lead          = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=20, choices=ActivityType.choices)
    note          = models.TextField()
    created_by    = models.ForeignKey("authentication.User", on_delete=models.SET_NULL, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "lead_activities"
        ordering = ["-created_at"]
