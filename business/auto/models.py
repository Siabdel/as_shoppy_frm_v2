# -*- coding: utf-8 -*-
"""
Automotive Product Models

This module defines the product models for the automotive business.
These inherit from the core BaseProduct and add automotive specific fields.
"""

from django.db import models
from django.utils.translation import gettext as _
from django.urls import reverse
from core.products.models import BaseProduct


class VehicleBrand(models.Model):
    """Vehicle brands/manufacturers."""
    
    name = models.CharField(max_length=100, verbose_name=_('Brand name'))
    slug = models.SlugField(max_length=100)
    logo = models.ImageField(upload_to='auto/brands/', null=True, blank=True)
    
    class Meta:
        verbose_name = _('Vehicle Brand')
        verbose_name_plural = _('Vehicle Brands')
    
    def __str__(self):
        return self.name


class VehicleModel(models.Model):
    """Vehicle models."""
    
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.CASCADE,
        related_name='models'
    )
    name = models.CharField(max_length=100, verbose_name=_('Model name'))
    slug = models.SlugField(max_length=100)
    
    class Meta:
        verbose_name = _('Vehicle Model')
        verbose_name_plural = _('Vehicle Models')
    
    def __str__(self):
        return f"{self.brand.name} {self.name}"


class AutoProduct(BaseProduct):
    """
    Automotive product model.
    
    Inherits from BaseProduct and adds automotive specific fields.
    Can represent vehicles, spare parts, or services.
    """
    
    # Product category
    PRODUCT_CATEGORIES = [
        ('vehicle', _('Vehicle')),
        ('spare_part', _('Spare Part')),
        ('accessory', _('Accessory')),
        ('service', _('Service')),
    ]
    auto_category = models.CharField(
        max_length=20,
        choices=PRODUCT_CATEGORIES,
        default='vehicle',
        verbose_name=_('Automotive category')
    )
    
    # Vehicle specific fields
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Brand')
    )
    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Model')
    )
    
    # Vehicle identification
    vin = models.CharField(
        max_length=17,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('VIN (Vehicle Identification Number)')
    )
    registration_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_('Registration number')
    )
    
    # Vehicle details
    year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Year')
    )
    mileage = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Mileage (km)')
    )
    
    # Fuel type
    FUEL_CHOICES = [
        ('gasoline', _('Gasoline')),
        ('diesel', _('Diesel')),
        ('electric', _('Electric')),
        ('hybrid', _('Hybrid')),
        ('lpg', _('LPG')),
        ('other', _('Other')),
    ]
    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Fuel type')
    )
    
    # Transmission
    TRANSMISSION_CHOICES = [
        ('manual', _('Manual')),
        ('automatic', _('Automatic')),
        ('semi_auto', _('Semi-Automatic')),
    ]
    transmission = models.CharField(
        max_length=20,
        choices=TRANSMISSION_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Transmission')
    )
    
    # Vehicle condition
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('used', _('Used')),
        ('refurbished', _('Refurbished')),
        ('for_parts', _('For Parts')),
    ]
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='used',
        verbose_name=_('Condition')
    )
    
    # Color
    color = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_('Color')
    )
    
    # Engine specs
    engine_power = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Engine power (HP)')
    )
    engine_capacity = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_('Engine capacity (L)')
    )
    
    # Spare part compatibility
    compatible_models = models.ManyToManyField(
        VehicleModel,
        blank=True,
        related_name='compatible_parts',
        verbose_name=_('Compatible vehicle models')
    )
    part_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('Part number')
    )
    manufacturer_part_number = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('Manufacturer part number')
    )
    
    # Warranty
    warranty_months = models.PositiveIntegerField(
        default=12,
        verbose_name=_('Warranty (months)')
    )
    
    # Vehicle status
    VEHICLE_STATUS = [
        ('available', _('Available')),
        ('reserved', _('Reserved')),
        ('sold', _('Sold')),
        ('in_repair', _('In Repair')),
        ('sold', _('Sold')),
    ]
    vehicle_status = models.CharField(
        max_length=20,
        choices=VEHICLE_STATUS,
        default='available',
        verbose_name=_('Vehicle status')
    )
    
    # Required for BaseProduct
    lookup_fields = ('id', 'slug')
    
    class Meta:
        verbose_name = _('Automotive Product')
        verbose_name_plural = _('Automotive Products')
    
    def __str__(self):
        if self.brand and self.model:
            return f"{self.brand.name} {self.model.name}"
        return self.name
    
    @property
    def product_type(self):
        return 'auto'
    
    def get_absolute_url(self):
        return reverse('auto:vehicle_detail', kwargs={'pk': self.pk})
    
    def get_price(self, request):
        """Return the price."""
        return self.price
    
    def managed_availability(self):
        """Automotive products use standard stock management."""
        return True
    
    def get_availability(self, request, **kwargs):
        """Check product availability."""
        from core.products.interfaces import Availability
        
        if self.vehicle_status == 'reserved':
            return Availability(
                is_available=False,
                message=_('Vehicle is reserved')
            )
        
        if self.vehicle_status == 'sold':
            return Availability(
                is_available=False,
                message=_('Vehicle has been sold')
            )
        
        if not self.is_active:
            return Availability(
                is_available=False,
                message=_('Product is not available')
            )
        
        return Availability(
            is_available=True,
            message=_('Available'),
            quantity=self.stock
        )


class VehicleImage(models.Model):
    """Images for vehicles."""
    
    vehicle = models.ForeignKey(
        AutoProduct,
        related_name='vehicle_images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='auto/vehicles/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('order', 'is_default')
    
    def __str__(self):
        return f"Image for {self.vehicle.name}"


class ServiceType(models.Model):
    """Types of automotive services."""
    
    name = models.CharField(max_length=100, verbose_name=_('Service name'))
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Base price')
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name=_('Duration (minutes)')
    )
    
    class Meta:
        verbose_name = _('Service Type')
        verbose_name_plural = _('Service Types')
    
    def __str__(self):
        return self.name


__all__ = [
    'VehicleBrand',
    'VehicleModel',
    'AutoProduct',
    'VehicleImage',
    'ServiceType',
]