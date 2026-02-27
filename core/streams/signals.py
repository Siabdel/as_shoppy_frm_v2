"""
Stream Signals Module

Signals for automatically creating stream events when certain actions occur.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Stream, StreamEvent
from .enums import EventType, StreamType
from core.orders.models import Order


@receiver(post_save, sender='project.Project')
def project_stream_handler(sender, instance, created, **kwargs):
    """Create stream events for project changes."""
    # Get or create project stream
    content_type = ContentType.objects.get_for_model(instance)
    stream, _ = Stream.objects.get_or_create(
        content_type=content_type,
        object_id=instance.pk,
        defaults={
            'name': f"Project: {instance.name}",
            'stream_type': StreamType.PROJECT,
            'is_active': True
        }
    )
    
    # Determine event type
    if created:
        event_type = EventType.PROJECT_CREATED
        description = f"Project '{instance.name}' was created"
    else:
        event_type = EventType.PROJECT_UPDATED
        description = f"Project '{instance.name}' was updated"
    
    # Create event
    StreamEvent.objects.create(
        stream=stream,
        event_type=event_type,
        description=description,
        actor=instance.author if hasattr(instance, 'author') else None,
        content_object=instance
    )


@receiver(post_save, sender=Order)
def order_stream_handler(sender, instance, created, **kwargs):
    """Create stream events for order changes."""
    content_type = ContentType.objects.get_for_model(instance)
    stream, _ = Stream.objects.get_or_create(
        content_type=content_type,
        object_id=instance.pk,
        defaults={
            'name': f"Order: #{instance.id}",
            'stream_type': StreamType.ORDER,
            'is_active': True
        }
    )
    
    if created:
        StreamEvent.objects.create(
            stream=stream,
            event_type=EventType.ORDER_CREATED,
            description=f"Order #{instance.id} was created",
            actor=instance.user,
            content_object=instance
        )