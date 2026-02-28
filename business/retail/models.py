# -*- coding: utf-8 -*-
"""
Retail Product Models

This module defines the product models for the retail e-commerce business.
These inherit from the core BaseProduct and add retail specific fields.
"""

from django.db import models
from django.utils.translation import gettext as _
from django.urls import reverse
from core.products.models import BaseProduct


class RetailProduct(BaseProduct):
    """
    Retail product model.
    
    Inherits from BaseProduct and adds retail specific fields.
    Uses StandardStockStrategy (standard quantity management).
    """
    
    # Product variants support
    has_variants = models.BooleanField(
        default=False,
        verbose_name=_('Has variants')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='variants',
        verbose_name=_('Parent product')
    )
    
    # Variant attributes
    sku = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('SKU')
    )
    barcode = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('Barcode')
    )
    
    # Size and color for variants
    size = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Size')
    )
    color = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Color')
    )
    
    # Inventory management
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Low stock threshold')
    )
    allow_backorder = models.BooleanField(
        default=False,
        verbose_name=_('Allow backorder')
    )
    track_inventory = models.BooleanField(
        default=True,
        verbose_name=_('Track inventory')
    )
    
    # Shipping
    is_shipping_required = models.BooleanField(
        default=True,
        verbose_name=_('Shipping required')
    )
    is_digital = models.BooleanField(
        default=False,
        verbose_name=_('Digital product')
    )
    digital_file = models.FileField(
        upload_to='retail/digital/',
        null=True,
        blank=True,
        verbose_name=_('Digital file')
    )
    
    # Weight for shipping calculation
    shipping_weight = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Shipping weight (kg)')
    )
    
    # Tax category
    tax_category = models.CharField(
        max_length=50,
        default='standard',
        verbose_name=_('Tax category')
    )
    
    # Status
    PRODUCT_STATUS = [
        ('available', _('Available')),
        ('out_of_stock', _('Out of Stock')),
        ('discontinued', _('Discontinued')),
        ('coming_soon', _('Coming Soon')),
    ]
    status = models.CharField(
        max_length=20,
        choices=PRODUCT_STATUS,
        default='available',
        verbose_name=_('Status')
    )
    
    # Required for BaseProduct
    lookup_fields = ('id', 'slug')
    
    class Meta:
        verbose_name = _('Retail Product')
        verbose_name_plural = _('Retail Products')
    
    def __str__(self):
        variant_info = ''
        if self.size:
            variant_info += f' - {self.size}'
        if self.color:
            variant_info += f' - {self.color}'
        return f"{self.name}{variant_info}"
    
    @property
    def product_type(self):
        return 'retail'
    
    def get_absolute_url(self):
        return reverse('retail:product_detail', kwargs={'pk': self.pk})
    
    def get_price(self, request):
        """Return the price, considering user groups and discounts."""
        from decimal import Decimal
        
        # Start with base price
        price = self.price
        
        # Check for discount price
        if self.discount_price and self.discount_price < self.price:
            price = self.discount_price
        
        # Apply user-specific pricing if applicable
        if request and request.user.is_authenticated:
            # Could implement customer-specific pricing here
            pass
        
        return price
    
    def managed_availability(self):
        """Retail products use standard stock management."""
        return self.track_inventory
    
    def get_availability(self, request, **kwargs):
        """Check product availability based on stock."""
        from core.products.interfaces import Availability
        
        if self.status == 'discontinued':
            return Availability(
                is_available=False,
                message=_('Product is discontinued')
            )
        
        if self.status == 'out_of_stock':
            if self.allow_backorder:
                return Availability(
                    is_available=True,
                    message=_('Available for backorder'),
                    quantity=0
                )
            return Availability(
                is_available=False,
                message=_('Out of stock'),
                quantity=0
            )
        
        if not self.is_active:
            return Availability(
                is_available=False,
                message=_('Product is not available')
            )
        
        if self.track_inventory:
            if self.stock <= 0:
                if self.allow_backorder:
                    return Availability(
                        is_available=True,
                        message=_('Available for backorder'),
                        quantity=0
                    )
                return Availability(
                    is_available=False,
                    message=_('Out of stock'),
                    quantity=0
                )
            
            if self.stock <= self.low_stock_threshold:
                return Availability(
                    is_available=True,
                    message=_('Low stock'),
                    quantity=self.stock
                )
            
            return Availability(
                is_available=True,
                message=_('In stock'),
                quantity=self.stock
            )
        
        # Digital products or products without tracking
        return Availability(
            is_available=True,
            message=_('Available'),
            quantity=999999
        )


class ProductVariant(BaseProduct):
    """
    Product variant model for retail products.
    
    Variants represent different combinations of attributes
    (size, color, etc.) for a parent product.
    """
    
    parent_product = models.ForeignKey(
        RetailProduct,
        on_delete=models.CASCADE,
        related_name='product_variants',
        verbose_name=_('Parent product')
    )
    
    class Meta:
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
    
    def __str__(self):
        return f"{self.parent_product.name} - {self.size} {self.color}"


class Wishlist(models.Model):
    """User wishlist for retail products."""
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    product = models.ForeignKey(
        RetailProduct,
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ('user', 'product')
        verbose_name = _('Wishlist Item')
        verbose_name_plural = _('Wishlist Items')
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


__all__ = [
    'RetailProduct',
    'ProductVariant',
    'Wishlist',
]