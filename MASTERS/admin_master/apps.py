from django.apps import AppConfig


class AdminMasterConfig(AppConfig):
    name = 'admin_master'

    def ready(self):
        try:
            from .bootstrap import ensure_dev_master_data
            ensure_dev_master_data()
        except Exception:
            return
