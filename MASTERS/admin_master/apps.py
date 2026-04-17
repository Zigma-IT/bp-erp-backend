"""Django app configuration for admin-master startup hooks."""

from django.apps import AppConfig


class AdminMasterConfig(AppConfig):
    name = 'admin_master'

    def ready(self):
        # Development bootstrap seeds screen/section records used by the UI.
        from .bootstrap import ensure_dev_master_data

        ensure_dev_master_data()
