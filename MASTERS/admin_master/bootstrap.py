"""Bootstrap helper for default admin-master seed data in development."""

import os

from django.conf import settings

from .models import MainScreen, ScreenSection


def ensure_dev_master_data() -> None:
    if not settings.DEBUG or os.environ.get("BP_SKIP_DEV_BOOTSTRAP") == "1":
        return

    masters_screen, _ = MainScreen.objects.get_or_create(
        name="Masters",
        defaults={"code": "masters", "status": True},
    )
    human_resource_screen, _ = MainScreen.objects.get_or_create(
        name="Human Resource",
        defaults={"code": "human-resource", "status": True},
    )
    operations_screen, _ = MainScreen.objects.get_or_create(
        name="Operations",
        defaults={"code": "operations", "status": True},
    )

    ScreenSection.objects.get_or_create(
        name="Admin Master",
        main_screen=masters_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Common Master",
        main_screen=masters_screen,
    )
    ScreenSection.objects.get_or_create(
        name="HR Master",
        main_screen=masters_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Human Resource Report",
        main_screen=human_resource_screen,
    )
    ScreenSection.objects.get_or_create(
        name="HR Document Templates Master",
        main_screen=human_resource_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Operations Master",
        main_screen=operations_screen,
    )
