"""Django app configuration for login/home startup hooks."""

from django.apps import AppConfig


class LoginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'login_home'

    def ready(self):
        try:
            from .bootstrap import ensure_dev_admin_user
            ensure_dev_admin_user()
        except Exception:
            return
