# -*- coding: utf-8 -*-
"""
Modèles CMagic Sport - Produits baskets et articles de sport

Héritage polymorphique du BaseProduct du core.
"""
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
    
    def get_specification_value(self, spec_name):
        """Retourne la valeur d'une spécification par son nom."""
        specs = self.get_specifications()
        spec_value = specs.filter(specification__name=spec_name).first()
        return spec_value.value if spec_value else None
    
    def get_brand(self):
        """Retourne la marque via les spécifications."""
        return self.get_specification_value('Brand')
    
    def get_model(self):
        """Retourne le modèle via les spécifications."""
        return self.get_specification_value('Model')
    
    def get_color(self):
        """Retourne la couleur via les spécifications."""
        return self.get_specification_value('Color')
    
    def get_material(self):
        """Retourne le matériau via les spécifications."""
        return self.get_specification_value('Material')
    
    def get_gender(self):
        """Retourne le genre via les spécifications."""
        return self.get_specification_value('Gender')
    
    def get_size(self):
        """Retourne la taille via les spécifications."""
        return self.get_specification_value('Size')
    
    def get_style_code(self):
        """Retourne le code style via les spécifications."""
        return self.get_specification_value('Style Code')
    
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
        """Retourne la liste des tailles disponibles."""
        if not self.available_sizes:
            return []
        return [s.strip() for s in self.available_sizes.split(',') if s.strip()]
    
    def get_size_display(self):
        """Retourne l'affichage des tailles."""
        sizes = self.get_size_list()
        return ', '.join(sizes) if sizes else ''


# ============================================
# Commandes (Orders)
# ============================================

class OrderStatus:
    """
    Statut de commande pour le suivi client.
    
    Workflow: PENDING -> PROCESSING -> SHIPPED -> DELIVERED
               ou: PENDING -> PROCESSING -> CANCELLED
    """
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    
    CHOICES = [
        (PENDING, _('En attente')),
        (PROCESSING, _('En cours de traitement')),
        (SHIPPED, _('Expédié')),
        (DELIVERED, _('Livré')),
        (CANCELLED, _('Annulé')),
        (REFUNDED, _('Remboursé')),
    ]
    
    # Step descriptions for tracking
    STEPS = {
        PENDING: {
            'title': _('Commande passée'),
            'description': _('Votre commande a été enregistrée'),
            'icon': 'bi-check-circle',
            'completed': True,
        },
        PROCESSING: {
            'title': _('En cours de préparation'),
            'description': _('Nous préparons votre commande'),
            'icon': 'bi-gear',
            'completed': True,
        },
        SHIPPED: {
            'title': _('Expédié'),
            'description': _('Votre commande est en cours de livraison'),
            'icon': 'bi-truck',
            'completed': False,
        },
        DELIVERED: {
            'title': _('Livré'),
            'description': _('Votre commande a été livrée'),
            'icon': 'bi-check2-all',
            'completed': False,
        },
    }
    
    @classmethod
    def get_default(cls):
        return cls.PENDING


class Order(models.Model):
    """
    Modèle de commande pour CMagic Sport.
    
    Permet au client de suivre sa commande et de consulter l'historique.
    """
    
    # Numéro de commande unique
    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Numéro de commande')
    )
    
    # Client (lié au Customer)
    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='cmagic_orders',
        verbose_name=_('Client')
    )
    
    # Informations client (copie pour historique)
    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Prénom')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Nom')
    )
    email = models.EmailField(
        verbose_name=_('Email')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Téléphone')
    )
    
    # Adresse de livraison
    shipping_address = models.TextField(
        verbose_name=_('Adresse de livraison')
    )
    shipping_city = models.CharField(
        max_length=100,
        verbose_name=_('Ville')
    )
    shipping_postal_code = models.CharField(
        max_length=20,
        verbose_name=_('Code postal')
    )
    shipping_country = models.CharField(
        max_length=100,
        default='France',
        verbose_name=_('Pays')
    )
    
    # Statut de la commande
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.CHOICES,
        default=OrderStatus.get_default,
        verbose_name=_('Statut')
    )
    
    # Suivi de livraison
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Numéro de suivi')
    )
    tracking_url = models.URLField(
        blank=True,
        verbose_name=_('URL de suivi')
    )
    carrier = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Transporteur')
    )
    
    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Dernière mise à jour')
    )
    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date d\'expédition')
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de livraison')
    )
    
    # Montants
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Sous-total')
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Frais de livraison')
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Montant taxes')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total')
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    class Meta:
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commande {self.order_number}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('cmagic_sport:order_detail', kwargs={'order_number': self.order_number})
    
    @property
    def is_paid(self):
        """Vérifie si la commande est payée."""
        return self.status != OrderStatus.CANCELLED
    
    @property
    def can_cancel(self):
        """Vérifie si la commande peut être annulée."""
        return self.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]
    
    @property
    def can_track(self):
        """Vérifie si le suivi est disponible."""
        return self.status in [OrderStatus.SHIPPED] and self.tracking_number
    
    def get_status_progress(self):
        """Retourne la progression du statut pour l'affichage."""
        status_order = [
            OrderStatus.PENDING,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ]
        
        if self.status == OrderStatus.CANCELLED:
            return {
                'current': _('Annulé'),
                'progress': 0,
                'steps': OrderStatus.STEPS,
            }
        
        if self.status == OrderStatus.REFUNDED:
            return {
                'current': _('Remboursé'),
                'progress': 0,
                'steps': OrderStatus.STEPS,
            }
        
        current_index = status_order.index(self.status) if self.status in status_order else 0
        progress = int((current_index / 3) * 100)
        
        # Update steps completion
        steps = {}
        for key, step in OrderStatus.STEPS.items():
            step_idx = status_order.index(key) if key in status_order else -1
            steps[key] = {
                **step,
                'completed': step_idx < current_index,
                'active': step_idx == current_index,
            }
        
        return {
            'current': self.get_status_display(),
            'progress': progress,
            'steps': steps,
        }


class OrderItem(models.Model):
    """
    Élément d'une commande (produit acheté).
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Commande')
    )
    
    product = models.ForeignKey(
        SportProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
        verbose_name=_('Produit')
    )
    
    # Informations du produit au moment de l'achat
    product_name = models.CharField(
        max_length=255,
        verbose_name=_('Nom du produit')
    )
    product_sku = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('SKU du produit')
    )
    product_size = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Taille')
    )
    product_color = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Couleur')
    )
    product_brand = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Marque')
    )
    
    # Prix
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Prix unitaire')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Quantité')
    )
    
    # Image du produit au moment de l'achat
    product_image = models.URLField(
        blank=True,
        verbose_name=_('URL de l\'image')
    )
    
    @property
    def total_price(self):
        """Retourne le prix total de l'élément."""
        return self.unit_price * self.quantity
    
    class Meta:
        verbose_name = _('Élément de commande')
        verbose_name_plural = _('Éléments de commande')
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
