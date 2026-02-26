"""
Django settings for django project in env DEV.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Configurations spécifiques au développement
# Par exemple, base de données de développement, outils de débogage, etc.
