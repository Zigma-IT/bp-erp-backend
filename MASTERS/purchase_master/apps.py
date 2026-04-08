from django.apps import AppConfig


class PurchaseMasterConfig(AppConfig):
    name = 'purchase_master'

    def ready(self):
        from .bootstrap import ensure_dev_purchase_master_data

        ensure_dev_purchase_master_data()
