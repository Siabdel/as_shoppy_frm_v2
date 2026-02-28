# -*- coding: utf-8 -*-
"""
Modèles CMagic Sport - Produits baskets et articles de sport

Héritage polymorphique du BaseProduct du core.
"""
from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from core.products.models import BaseProduct
from product.models import ProductType


# ============================================
# Modèle principal
# ============================================

class SportProduct(BaseProduct):
    """
    Produit spécifique baskets et articles de sport.
    
    Utilise les tables existantes:
    - product.ProductImage (images)
    - product.ProductSpecificationValue (spécifications)
    """
    
    # Note: category is inherited from BaseProduct
    
    # Type de produit
    product_type = models.ForeignKey(
        ProductType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sport_products',
        verbose_name=_('Type de produit')
    )
    
    # Tailles disponibles
    available_sizes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Tailles disponibles'),
        help_text=_('Tailles: 38,39,40,41,42,43')
    )
    
    # Collection
    collection_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Année de collection')
    )
    
    # Édition limitée
    is_limited_edition = models.BooleanField(
        default=False,
        verbose_name=_('Édition limitée')
    )
    
    # Promotion saisonnière
    is_season_promo = models.BooleanField(
        default=False,
        verbose_name=_('Promotion saisonnière')
    )
    
    season_promo_discount = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Réduction saisonnière (%)')
    )
    
    class Meta:
        verbose_name = _('Produit Sport')
        verbose_name_plural = _('Produits Sport')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name}"
    
    def get_absolute_url(self):
        return reverse(
            'cmagic_sport:product_detail',
            kwargs={'slug': self.slug}
        )
    
    def get_price(self, request=None):
        from decimal import Decimal as D
        base_price = D(str(self.price))
        
        if self.is_season_promo and self.season_promo_discount > 0:
            discount_factor = D(str(1 - self.season_promo_discount / 100))
            base_price = base_price * discount_factor
        
        return float(base_price.quantize(D('0.01')))
    
    def get_availability(self, request=None, **kwargs):
        from core.products.interfaces import Availability
        
        is_available = self.in_stock and self.available and self.stock > 0
        
        return Availability(
            is_available=is_available,
            quantity=self.stock,
            message='' if is_available else _('Rupture de stock')
        )
    
    def get_stock_available(self):
        return self.stock
    
    def managed_availability(self):
        return True
    
    def get_specifications(self):
        """Retourne les spécifications via la relation polymorphique."""
        from product.models import ProductSpecificationValue
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(self)
        return ProductSpecificationValue.objects.filter(
            product_content_type=content_type,
            product_object_id=self.pk
        )
    
    def get_images(self):
        """Retourne les images via la relation polymorphique."""
        from product.models import ProductImage
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(self)
        return ProductImage.objects.filter(
            product_content_type=content_type,
            product_object_id=self.pk
        )
    
    def get_primary_image(self):
        """Retourne l'image principale."""
        images = self.get_images()
        primary = images.filter(is_primary=True).first()
        if primary:
            return primary
        return images.first()
    
    def get_size_list(self):
        if not self.available_sizes:
            return []
        return [s.strip() for s in self.available_sizes.split(',') if s.strip()]
        if primary:
            return primary
        return images.first()
    
    def get_size_list(self):
        if not self.available_sizes:
            return []
        return [s.strip() for s in self.available_sizes.split(',') if s.strip()]