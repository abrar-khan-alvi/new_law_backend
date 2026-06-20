from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Auto-create a free subscription on user creation.
        import accounts.signals  # noqa: F401
