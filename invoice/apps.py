from django.apps import AppConfig
from django.dispatch import Signal

class InvoicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "invoice"

    def ready(self):
        import invoice.signals  # noqa F401
        # Empty Cart
        # Create a custom signal
        checkout_completed = Signal()