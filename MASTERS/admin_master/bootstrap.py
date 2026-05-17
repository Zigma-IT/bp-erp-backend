"""Bootstrap helper for default admin-master seed data in development."""

import os

from django.conf import settings

from .models import MainScreen, ScreenSection


def ensure_dev_master_data() -> None:
    if not settings.DEBUG or os.environ.get("BP_SKIP_DEV_BOOTSTRAP") == "1":
        return

    masters_screen, _ = MainScreen.objects.get_or_create(
        name="Masters",
        defaults={
            "code": "masters",
            "folder_key": "masters",
            "screen_type": "Mega Menu",
            "order_no": 1,
            "status": True,
        },
    )
    human_resource_screen, _ = MainScreen.objects.get_or_create(
        name="Human Resource",
        defaults={
            "code": "human-resource",
            "folder_key": "human-resource",
            "screen_type": "Mega Menu",
            "order_no": 3,
            "status": True,
        },
    )
    procurement_screen, _ = MainScreen.objects.get_or_create(
        name="Procurement",
        defaults={
            "code": "procurement",
            "folder_key": "procurement",
            "screen_type": "Mega Menu",
            "order_no": 2,
            "status": True,
        },
    )
    operations_screen, _ = MainScreen.objects.get_or_create(
        name="Operations",
        defaults={
            "code": "operations",
            "folder_key": "operations",
            "screen_type": "Mega Menu",
            "order_no": 4,
            "status": True,
        },
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
        name="Purchase Entry's",
        main_screen=procurement_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Approvals",
        main_screen=procurement_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Reports",
        main_screen=procurement_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Sales",
        main_screen=procurement_screen,
    )
    ScreenSection.objects.get_or_create(
        name="Operations Master",
        main_screen=operations_screen,
    )
