from django.conf import settings
from django.contrib.auth.models import User


def ensure_dev_admin_user() -> None:
    if not settings.DEBUG:
        return

    username = "admin"
    password = "admin123"

    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
            "email": "",
        },
    )

    dirty = False
    if not user.is_staff:
        user.is_staff = True
        dirty = True
    if not user.is_superuser:
        user.is_superuser = True
        dirty = True
    if not user.is_active:
        user.is_active = True
        dirty = True

    user.set_password(password)
    dirty = True

    if dirty:
        user.save()
