# -*- coding: utf-8 -*-
"""
Real Estate Product Models

This module defines the product models for the real estate business.
These inherit from the core BaseProduct and add real estate specific fields.
"""

from django.db import models
from django.utils.translation import gettext as _
from django.urls import reverse
from core.products.models import BaseProduct
from core import deferred


class PropertyType(models.Model):
    """Types of real estate properties."""
    
    name = models.CharField(max_length=100, verbose_name=_('Property type'))
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Property Type')
        verbose_name_plural = _('Property Types')
    
    def __str__(self):
        return self.name


class ImmoProduct(BaseProduct):
    """
    Real estate product model.
    
    Inherits from BaseProduct and adds real estate specific fields.
    Uses NoStockStrategy (no stock management for unique properties).
    """
    
    # Property type classification
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Property type')
    )
    
    # Property details
    surface_area = models.FloatField(
        verbose_name=_('Surface area (m²)')
    )
    land_area = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Land area (m²)')
    )
    rooms = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Number of rooms')
    )
    bedrooms = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Number of bedrooms')
    )
    bathrooms = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Number of bathrooms')
    )
    floor = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Floor')
    )
    total_floors = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Total floors in building')
    )
    
    # Location
    address = models.CharField(
        max_length=255,
        verbose_name=_('Address')
    )
    city = models.CharField(
        max_length=100,
        verbose_name=_('City')
    )
    postal_code = models.CharField(
        max_length=20,
        verbose_name=_('Postal code')
    )
    country = models.CharField(
        max_length=100,
        default='France',
        verbose_name=_('Country')
    )
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Property features
    has_elevator = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    has_terrace = models.BooleanField(default=False)
    has_garage = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_cellar = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_heating = models.BooleanField(default=True)
    
    # Heating type
    HEATING_CHOICES = [
        ('gas', _('Gas')),
        ('electric', _('Electric')),
        ('oil', _('Oil')),
        ('heat_pump', _('Heat Pump')),
        ('other', _('Other')),
    ]
    heating_type = models.CharField(
        max_length=20,
        choices=HEATING_CHOICES,
        default='gas',
        verbose_name=_('Heating type')
    )
    
    # Energy performance
    energy_class = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'),
            ('E', 'E'), ('F', 'F'), ('G', 'G'),
        ],
        null=True,
        blank=True,
        verbose_name=_('Energy class')
    )
    ges_class = models.CharField(
        max_length=1,
        choices=[
            ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'),
            ('E', 'E'), ('F', 'F'), ('G', 'G'),
        ],
        null=True,
        blank=True,
        verbose_name=_('GES class')
    )
    
    # Transaction type
    TRANSACTION_CHOICES = [
        ('sale', _('For Sale')),
        ('rent', _('For Rent')),
        ('rent_to_own', _('Rent to Own')),
    ]
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_CHOICES,
        default='sale',
        verbose_name=_('Transaction type')
    )
    
    # Rental specific
    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Monthly rent')
    )
    rental_charges = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Monthly rental charges')
    )
    security_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Security deposit')
    )
    
    # Mandate (selling contract)
    mandate_start = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Mandate start date')
    )
    mandate_end = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Mandate end date')
    )
    mandate_type = models.CharField(
        max_length=20,
        choices=[
            ('exclusive', _('Exclusive')),
            ('simple', _('Simple')),
        ],
        null=True,
        blank=True,
        verbose_name=_('Mandate type')
    )
    
    # Availability status
    is_reserved = models.BooleanField(
        default=False,
        verbose_name=_('Reserved')
    )
    reserved_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Reserved until')
    )
    
    # Required for BaseProduct
    lookup_fields = ('id', 'slug')
    
    class Meta:
        verbose_name = _('Property')
        verbose_name_plural = _('Properties')
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    @property
    def product_type(self):
        return 'immo'
    
    def get_absolute_url(self):
        return reverse('immo:property_detail', kwargs={'pk': self.pk})
    
    def get_price(self, request):
        """Return the price (sale price or monthly rent)."""
        if self.transaction_type == 'rent':
            return self.monthly_rent or 0
        return self.price
    
    def managed_availability(self):
        """Real estate doesn't use standard stock management."""
        return False
    
    def get_availability(self, request, **kwargs):
        """Check property availability."""
        from core.products.interfaces import Availability
        
        if self.is_reserved:
            return Availability(
                is_available=False,
                message=_('Property is currently reserved')
            )
        
        if not self.is_active:
            return Availability(
                is_available=False,
                message=_('Property is not available')
            )
        
        return Availability(
            is_available=True,
            message=_('Available'),
            quantity=1  # One unique property
        )


class PropertyImage(models.Model):
    """Images for real estate properties."""
    
    property = models.ForeignKey(
        ImmoProduct,
        related_name='property_images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='immo/properties/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('order', 'is_default')
    
    def __str__(self):
        return f"Image for {self.property.name}"


class Visit(models.Model):
    """Property visit scheduling."""
    
    property = models.ForeignKey(
        ImmoProduct,
        related_name='visits',
        on_delete=models.CASCADE
    )
    customer = deferred.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='property_visits'
    )
    visit_date = models.DateTimeField(verbose_name=_('Visit date'))
    notes = models.TextField(blank=True)
    is_confirmed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ('-visit_date',)
        verbose_name = _('Visit')
        verbose_name_plural = _('Visits')
    
    def __str__(self):
        return f"Visit: {self.property.name} - {self.visit_date}"


__all__ = [
    'PropertyType',
    'ImmoProduct',
    'PropertyImage',
    'Visit',
]