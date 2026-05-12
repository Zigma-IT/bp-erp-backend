"""Bootstrap helper for shared common-master seed data in development."""

import os

from django.conf import settings

from .models import CommonMaster, Continent


def ensure_dev_common_master_data() -> None:
    if not settings.DEBUG or os.environ.get("BP_SKIP_DEV_BOOTSTRAP") == "1":
        return

    for continent_name in [
        "Asia",
        "Europe",
        "Africa",
        "North America",
        "South America",
        "Antarctica",
        "Australia",
    ]:
        Continent.objects.get_or_create(name=continent_name, defaults={"status": True})

    for city_type in ["Metro", "Urban", "Rural"]:
        CommonMaster.objects.get_or_create(
            type="CITY_TYPE",
            name=city_type,
            defaults={"is_active": True},
        )

    for application_type in [
        "Web Application",
        "Mobile Application",
        "Desktop Application",
    ]:
        CommonMaster.objects.get_or_create(
            type="APPLICATION_TYPE",
            name=application_type,
            defaults={"is_active": True},
        )

    for document_type in [
        "PAN",
        "GST",
        "Aadhar",
        "Passport",
        "License",
        "Bank Verification Certificate",
    ]:
        CommonMaster.objects.get_or_create(
            type="DOCUMENT_TYPE",
            name=document_type,
            defaults={"is_active": True},
        )

    for supplier_group in ["Manufacturer", "Dealer", "Service Provider"]:
        CommonMaster.objects.get_or_create(
            type="SUPPLIER_GROUP",
            name=supplier_group,
            defaults={"is_active": True},
        )

    for msme_type in ["Micro", "Small", "Medium"]:
        CommonMaster.objects.get_or_create(
            type="MSME_TYPE",
            name=msme_type,
            defaults={"is_active": True},
        )
