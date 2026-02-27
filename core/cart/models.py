# -*- coding: utf-8 -*-
"""
Core Cart Module - Base Models

This module contains the base cart and cart item models that use
deferred foreign keys to support polymorphic product relations.

The deferred foreign key pattern allows business applications to add
new product types without requiring migrations on the core cart models.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from core import deferred
from core.products.models import BaseProduct


class BaseCartItemModel(models.Model):
    """
    Abstract base model for cart items.
    
    Uses ContentTypes (GenericForeignKey) to support any product type
    without requiring migrations when new product types are added.
    """
    
    # Polymorphic product reference using ContentTypes
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__startswith': 'product'},
    )
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    
    # Cart item fields
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name=_('Unit price at time of adding')
    )
    
    # Timestamps
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ('-added_at',)
    
    @property
    def total_price(self):
        """Calculate total price for this cart item."""
        return self.quantity * self.unit_price
    
    def __str__(self):
        return f"{self.product} x {self.quantity}"


class BaseCartModel(models.Model):
    """
    Abstract base model for shopping carts.
    """
    
    # Cart identification
    cart_key = models.CharField(
        max_length=255, 
        unique=True,
        verbose_name=_('Cart key')
    )
    
    # Customer reference (optional - supports anonymous carts)
    customer = deferred.ForeignKey(
        'customer.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='carts',
    )
    
    # Session key for anonymous carts
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    
    # Cart status
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    
    # Expiration
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expiration date')
    )
    
    # Totals (cached for performance)
    total_items = models.PositiveIntegerField(default=0)
    total_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name=_('Total price')
    )
    
    class Meta:
        abstract = True
        ordering = ('-updated_at',)
    
    def __str__(self):
        return f"Cart {self.cart_key}"
    
    def is_expired(self):
        """Check if the cart has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    def get_items(self):
        """
        Get all active items in the cart.
        Subclasses should override to return the correct related manager.
        """
        return []
    
    def add_product(self, product, quantity=1):
        """
        Add a product to the cart.
        
        Args:
            product: The product to add
            quantity: Quantity to add
            
        Returns:
            CartItem: The created/updated cart item
        """
        raise NotImplementedError(
            "Subclasses must implement add_product()"
        )
    
    def remove_product(self, product):
        """
        Remove a product from the cart.
        
        Args:
            product: The product to remove
            
        Returns:
            bool: True if removed
        """
        raise NotImplementedError(
            "Subclasses must implement remove_product()"
        )
    
    def clear(self):
        """Clear all items from the cart."""
        raise NotImplementedError(
            "Subclasses must implement clear()"
        )
    
    def update_totals(self):
        """Update cached totals."""
        raise NotImplementedError(
            "Subclasses must implement update_totals()"
        )
    
    def to_quote(self, request):
        """
        Convert cart to a quote (Devis).
        
        This is the Cart -> Quote step in the workflow.
        
        Args:
            request: HTTP request
            
        Returns:
            Quote: The created quote
        """
        raise NotImplementedError(
            "Subclasses must implement to_quote()"
        )


# Aliases for backward compatibility
BaseCart = BaseCartModel
BaseCartItem = BaseCartItemModel


__all__ = [
    'BaseCart',
    'BaseCartItem',
    'BaseCartModel',
    'BaseCartItemModel',
]
