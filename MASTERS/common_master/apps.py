from django.apps import AppConfig


class CommonMasterConfig(AppConfig):
    name = 'common_master'

    def ready(self):
        try:
            from .bootstrap import ensure_dev_common_master_data
            ensure_dev_common_master_data()
        except Exception:
            return
