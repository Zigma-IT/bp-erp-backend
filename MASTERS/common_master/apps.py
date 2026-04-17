"""Django app configuration for common-master startup hooks."""

from django.apps import AppConfig


class CommonMasterConfig(AppConfig):
    name = 'common_master'

    def ready(self):
        # Development bootstrap seeds basic lookup records like continents.
        from .bootstrap import ensure_dev_common_master_data

        ensure_dev_common_master_data()
