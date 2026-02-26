from django.apps import AppConfig


class ImmoShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'immoshop'

    def ready(self):
        #from . import signals
        pass
