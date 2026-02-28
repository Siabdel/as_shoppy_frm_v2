# -*- coding: utf-8 -*-
from django.apps import AppConfig


class CmagicSportConfig(AppConfig):
    """Configuration de l'application CMagic Sport."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cmagic_sport'
    verbose_name = 'CMagic Sport - Boutique Baskets'
    
    def ready(self):
        """Hook appelé quand l'application est chargée."""
        # Import des signaux si nécessaire
        pass