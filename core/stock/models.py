# -*- coding: utf-8 -*-
"""
Core Stock Module - Models

This module contains stock management models for tracking:
- Stock movements (history of all stock changes)
- Stock reservations (temporary holds for orders)
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class StockMovement(models.Model):
    """
    Track all stock movements for audit purposes.
    
    Records every change in stock quantity with:
    - Product reference
    - Quantity change (+ for increase, - for decrease)
    - Reason for change
    - Reference (order, return, etc.)
    - Timestamp
    """
    
    # Polymorphic product reference
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__startswith': 'product'},
    )
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    
    # Movement details
    quantity = models.IntegerField(
        verbose_name=_('Quantity change')
    )
    reason = models.CharField(
        max_length=50,
        choices=[
            ('sale', _('Sale')),
            ('return', _('Return')),
            ('restock', _('Restock')),
            ('adjustment', _('Adjustment')),
            ('damage', _('Damage')),
            ('loss', _('Loss')),
            ('reservation', _('Reservation')),
            ('reservation_release', _('Reservation Release')),
        ],
        verbose_name=_('Reason')
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Reference')
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
    
    def __str__(self):
        sign = '+' if self.quantity > 0 else ''
        return f"{self.product} {sign}{self.quantity} - {self.reason}"


class StockReservation(models.Model):
    """
    Temporary stock reservations for orders.
    
    When an order is placed, stock is reserved to prevent
    overselling. Reservations are either:
    - Converted to permanent decrement (on delivery)
    - Released (on order cancellation)
    """
    
    # Polymorphic product reference
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__startswith': 'product'},
    )
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    
    # Reservation details
    quantity = models.PositiveIntegerField(
        verbose_name=_('Reserved quantity')
    )
    order_id = models.CharField(
        max_length=255,
        verbose_name=_('Order ID')
    )
    
    # Status
    STATUS_CHOICES = [
        ('reserved', _('Reserved')),
        ('converted', _('Converted to Sale')),
        ('released', _('Released')),
        ('expired', _('Expired')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='reserved',
        verbose_name=_('Status')
    )
    
    # Expiration (reservations expire after 24 hours by default)
    expires_at = models.DateTimeField(
        verbose_name=_('Expires at')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Stock Reservation')
        verbose_name_plural = _('Stock Reservations')
    
    def __str__(self):
        return f"{self.product} x{self.quantity} - {self.order_id}"
    
    def is_expired(self):
        """Check if reservation has expired."""
        return timezone.now() > self.expires_at
    
    def convert_to_sale(self):
        """Convert reservation to permanent sale."""
        if self.status == 'reserved':
            self.status = 'converted'
            self.converted_at = timezone.now()
            self.save()
    
    def release(self):
        """Release the reservation."""
        if self.status == 'reserved':
            self.status = 'released'
            self.released_at = timezone.now()
            self.save()


__all__ = [
    'StockMovement',
    'StockReservation',
]