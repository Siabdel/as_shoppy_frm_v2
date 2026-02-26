import os

# Définissez une variable d'environnement DJANGO_SETTINGS_MODULE
# pour contrôler quelle configuration utiliser
environment = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *
