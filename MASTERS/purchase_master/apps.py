"""Django app configuration for purchase-master startup hooks."""

from django.apps import AppConfig


class PurchaseMasterConfig(AppConfig):
    name = 'purchase_master'

    def ready(self):
        # Development bootstrap seeds companies referenced by purchase masters.
        from .bootstrap import ensure_dev_purchase_master_data

        ensure_dev_purchase_master_data()
