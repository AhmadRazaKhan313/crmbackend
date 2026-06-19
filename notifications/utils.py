from .models import Notification


def notify(tenant, recipient, type, title, message="", link=""):
    if recipient is None:
        return None
    return Notification.objects.create(
        tenant=tenant, recipient=recipient,
        type=type, title=title, message=message, link=link,
    )


def notify_many(tenant, recipients, type, title, message="", link=""):
    Notification.objects.bulk_create([
        Notification(
            tenant=tenant, recipient=r,
            type=type, title=title, message=message, link=link,
        )
        for r in recipients if r is not None
    ])
