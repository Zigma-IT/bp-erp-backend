from django.conf import settings

from .models import Company


def ensure_dev_purchase_master_data() -> None:
    if not settings.DEBUG:
        return

    for company_name in ["Blue Planet", "TATA"]:
        Company.objects.get_or_create(company_name=company_name)
