# -*- coding: utf-8 -*-
"""
Core Products Module - Base Models

This module contains the base product model that all business applications
inherit from. It uses polymorphic models to support different product types
while maintaining a stable core interface.

The deferred foreign key pattern is used to allow business apps to define
their own product models without requiring core migrations.
"""

import os
from django.utils import timezone
from django.db import models
from django.core.cache import cache
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.conf import settings
from django_resized import ResizedImageField
from polymorphic.models import PolymorphicModel, PolymorphicManager

from core import deferred
from core.taxonomy.models import TaggedItem, MPCategory
from core.products.interfaces import (
    ProductInterface,
    Availability,
    PricingInterface,
    StockInterface,
)


class BaseProductManager(PolymorphicManager):
    """Manager for BaseProduct that filters by is_active by default."""
    
    def get_queryset(self):
        return super(BaseProductManager, self).get_queryset().filter(is_active=True)
    
    def get_all_products(self):
        """Get all products including inactive ones."""
        return super().get_queryset()


class PolymorphicProductMetaclass(deferred.PolymorphicForeignKeyBuilder):
    """
    Metaclass for BaseProduct that performs safety checks
    and handles deferred foreign key resolution.
    """
    
    @classmethod
    def perform_meta_model_check(cls, Model):
        """
        Perform safety checks on the ProductModel being created.
        """
        if not isinstance(Model.objects, BaseProductManager):
            msg = "Class `{}.objects` must provide ModelManager inheriting from BaseProductManager"
            raise NotImplementedError(msg.format(Model.__name__))
        
        if not isinstance(getattr(Model, 'lookup_fields', None), (list, tuple)):
            msg = "Class `{}` must provide a tuple of `lookup_fields` so that we can easily lookup for Products"
            raise NotImplementedError(msg.format(Model.__name__))
        
        if not callable(getattr(Model, 'get_price', None)):
            msg = "Class `{}` must provide a method implementing `get_price(request)`"
            raise NotImplementedError(msg.format(cls.__name__))


class BaseProduct(PolymorphicModel):
    """
    Abstract base product model for the framework.
    
    All business applications should inherit from this model to create
    their specific product types (ImmoProduct, AutoProduct, RetailProduct, etc.)
    
    Key Features:
    - Polymorphic: Supports different product types via ContentTypes
    - Deferred Foreign Keys: Business apps can extend without core migrations
    - Hook System: Subclasses must implement required methods
    - Generic Relations: Support for tags, images, and attachments
    
    Subclasses MUST implement:
    - get_absolute_url(): Canonical URL for the product
    - get_price(request): Current price with potential user-specific variations
    
    Subclasses MAY override:
    - get_availability(): Stock availability check
    - managed_availability(): Whether stock is managed for this product
    """
    
    # Core product fields
    # Note: Each subclass should override this with a unique related_name
    # to avoid clashes between different product models
    category = models.ForeignKey(
        MPCategory,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Pricing fields
    price = models.DecimalField(max_digits=10, decimal_places=2)
    regular_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Availability
    available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(
        _('Active'), 
        default=True, 
        help_text=_("Is this product publicly visible.")
    )
    
    # Product identification
    product_code = models.CharField(
        _("Product code"), 
        max_length=255, 
        editable=False,
        unique=True,
        null=True, 
        blank=True,
        help_text=_("Product code of added item."),
    )
    ean13 = models.CharField(max_length=13, blank=True, verbose_name=_('EAN13'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Media
    default_image = ResizedImageField(
        upload_to='upload/product_images/%Y/%m/', 
        blank=True
    )
    
    # Units of Measure
    uom = models.CharField(
        max_length=20, 
        choices=settings.PRODUCT_UOM_CHOICES, 
        default=settings.PRODUCT_DEFAULT_UOM, 
        verbose_name=_('UOM')
    )
    uos = models.CharField(
        max_length=20, 
        choices=settings.PRODUCT_UOM_CHOICES, 
        default=settings.PRODUCT_DEFAULT_UOM, 
        verbose_name=_('UOS')
    )
    uom_to_uos = models.FloatField(
        default=1.0, 
        help_text=_('Conversion rate between UOM and UOS'), 
        verbose_name=_('UOM to UOS')
    )
    
    # Physical properties
    weight = models.FloatField(default=1.0, verbose_name=_('unit weight (Kg)'))
    
    # Product type flags
    is_consumable = models.BooleanField(default=False, verbose_name=_('consumable?'))
    is_service = models.BooleanField(default=False, verbose_name=_('service?'))
    
    # Sales configuration
    sales_price = models.FloatField(default=0.0, verbose_name=_('sales price'))
    sales_currency = models.CharField(
        max_length=3,
        choices=settings.CURRENCIES.choices, 
        default=settings.DEFAULT_CURRENCY, 
        verbose_name=_('sales currency')
    )
    max_sales_discount = models.FloatField(default=0.0, verbose_name=_('max sales discount (%)'))
    sales_tax = models.FloatField(default=0.0, verbose_name=_('sales tax (%)'))
    
    # Generic relations
    tags = GenericRelation('taxonomy.Tag', null=True, blank=True, verbose_name=_('tags'))
    
    # Manager
    objects = BaseProductManager()
    
    # Required for polymorphic lookup
    lookup_fields = ('id', 'slug')
    
    class Meta:
        abstract = True
        ordering = ('name', )
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    
    def __str__(self):
        return self.name
    
    @property
    def product_model(self):
        """
        Returns the polymorphic model name of the product's class.
        """
        return self.polymorphic_ctype.model
    
    def generate_number(self):
        """Generate a unique product code."""
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        new_number = f"PR-{year}{month}{day}-{self.pk:06d}"
        return new_number
    
    def save(self, *args, **kwargs):
        # Save first to get a PK
        super().save(*args, **kwargs)
        
        # Generate and save product code if not already done
        if not self.product_code:
            self.product_code = self.generate_number()
            super().save(update_fields=['product_code'])
    
    def augment_quantity(self, quantity):
        """Increase product quantity."""
        self.stock = self.stock + int(quantity)
        self.save()
    
    def default_image_exist(self):
        """Check if default image exists."""
        output_dir = os.path.join(settings.BASE_DIR, self.default_image.url)
        return not os.path.exists(output_dir)
    
    # ====================
    # HOOK METHODS
    # These must be implemented by subclasses
    # ====================
    
    def get_absolute_url(self):
        """
        Hook for returning the canonical Django URL of this product.
        """
        msg = "Method get_absolute_url() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))
    
    def get_price(self, request):
        """
        Hook for returning the current price of this product.
        The price shall be of type Money.
        
        Use the `request` object to vary the price according to:
        - Logged in user
        - User type (B2B vs B2C)
        - Country code
        - Language
        """
        msg = "Method get_price() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))
    
    def get_product_variant(self, **kwargs):
        """
        Hook for returning the variant of a product using parameters passed in by **kwargs.
        If the product has no variants, then return the product itself.
        """
        return self
    
    def get_product_variants(self):
        """
        Hook for returning a queryset of variants for the given product.
        If the product has no variants, then the queryset contains just itself.
        """
        return self._meta.model.objects.filter(pk=self.pk)
    
    def get_availability(self, request, **kwargs):
        """
        Hook for checking the availability of a product.
        
        Returns an Availability object.
        """
        return Availability(
            is_available=self.in_stock and self.available,
            quantity=self.stock,
            message='' if self.in_stock else _('Out of stock')
        )
    
    def managed_availability(self):
        """
        Return True if this product has its quantity managed by some inventory functionality.
        
        Override this for products that don't need stock management
        (e.g., real estate, services).
        """
        return True
    
    def is_in_cart(self, cart, watched=False, **kwargs):
        """
        Checks if the current product is already in the given cart.
        
        Returns the corresponding cart_item if found, None otherwise.
        """
        from shop import models as sh_models
        cart_item_qs = sh_models.CartItem.objects.filter(cart=cart, product=self)
        if cart_item_qs.exists():
            return cart_item_qs.first()
        return None


class BaseImage(models.Model):
    """
    Abstract base model for product images.
    Business applications can extend this for their specific image needs.
    """
    
    image = ResizedImageField(upload_to='product_images/%Y/%m/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
        ordering = ('-is_default', 'created_at')


class BaseProductSpecification(models.Model):
    """
    Abstract base model for product specifications/attributes.
    """
    
    name = models.CharField(max_length=150, db_index=True)
    value = models.CharField(max_length=255)
    
    class Meta:
        abstract = True


# Import availability for type hints
__all__ = [
    'BaseProduct',
    'BaseProductManager',
    'PolymorphicProductMetaclass',
    'BaseImage',
    'BaseProductSpecification',
    'ProductInterface',
    'Availability',
    'PricingInterface',
    'StockInterface',
]