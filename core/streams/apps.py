from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class StreamsConfig(AppConfig):
    """Configuration for the streams application."""
    
    name = 'core.streams'
    label = 'streams'
    verbose_name = _('Streams & Milestones')
    
    def ready(self):
        """Initialize signals when the app is ready."""
        from . import signals