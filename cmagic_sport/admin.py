# -*- coding: utf-8 -*-
"""
Configuration admin pour CMagic Sport.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _

from .models import SportProduct


@admin.register(SportProduct)
class SportProductAdmin(admin.ModelAdmin):
    """
    Admin pour les produits sport.
    """
    
    # Configuration de la liste
    list_display = [
        'thumbnail',
        'name',
        'product_type_display',
        'price_display',
        'stock_status',
        'in_stock',
        'is_active',
        'created_at',
    ]
    
    list_display_links = ['thumbnail', 'name']
    
    list_filter = [
        'product_type',
        'in_stock',
        'is_active',
        'is_limited_edition',
        'is_season_promo',
        'collection_year',
    ]
    
    search_fields = [
        'name',
        'product_code',
    ]
    
    list_editable = [
        'in_stock',
        'is_active',
    ]
    
    # Configuration des formulaires
    fieldsets = (
        (_('Informations principales'), {
            'fields': (
                'name',
                'slug',
                'description',
            )
        }),
        (_('Type et collection'), {
            'fields': (
                'product_type',
                'collection_year',
                'is_limited_edition',
            )
        }),
        (_('Tailles'), {
            'fields': (
                'available_sizes',
            )
        }),
        (_('Prix'), {
            'fields': (
                ('price', 'regular_price', 'discount_price'),
                ('is_season_promo', 'season_promo_discount'),
            )
        }),
        (_('Stock'), {
            'fields': (
                ('stock', 'in_stock', 'available'),
            )
        }),
        (_('Médias'), {
            'fields': (
                'default_image',
            )
        }),
        (_('Options'), {
            'fields': (
                'is_active',
                'is_consumable',
                'is_service',
            )
        }),
    )
    
    prepopulated_fields = {
        'slug': ('name',)
    }
    
    readonly_fields = [
        'product_code',
        'created_at',
        'updated_at',
    ]
    
    # Actions personnalisées
    actions = [
        'mark_as_active',
        'mark_as_inactive',
        'apply_season_promo',
    ]
    
    def thumbnail(self, obj):
        """Affiche une miniature de l'image du produit."""
        primary_image = obj.get_primary_image()
        if primary_image and hasattr(primary_image, 'image') and primary_image.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: auto; '
                'border-radius: 4px;" />',
                primary_image.image.url
            )
        if obj.default_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: auto; '
                'border-radius: 4px;" />',
                obj.default_image.url
            )
        return format_html(
            '<span style="color: #999;">{}</span>',
            _('Pas d\'image')
        )
    thumbnail.short_description = _('Image')
    
    def price_display(self, obj):
        """Affiche le prix formaté."""
        price = obj.get_price()
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            price_value = 0
        return format_html(
            '<strong>{} €</strong>',
            f"{price_value:.2f}"
        )
    price_display.short_description = _('Prix')
    
    def stock_status(self, obj):
        """Affiche le statut du stock avec couleur."""
        if obj.stock > 10:
            color = 'green'
            text = _('En stock')
        elif obj.stock > 0:
            color = 'orange'
            text = _('Stock faible')
        else:
            color = 'red'
            text = _('Rupture')
        
        return format_html(
            '<span style="color: {};">{} ({})</span>',
            color,
            text,
            obj.stock
        )
    stock_status.short_description = _('Stock')
    
    def product_type_display(self, obj):
        """Affiche le type de produit."""
        return obj.product_type.name if obj.product_type else '-'
    product_type_display.short_description = _('Type')
    
    # Actions personnalisées
    def mark_as_active(self, request, queryset):
        """Marque les produits comme actifs."""
        queryset.update(is_active=True)
        self.message_user(
            request,
            _('%d produits ont été marqués comme actifs.') % queryset.count()
        )
    mark_as_active.short_description = _('Marquer comme actif')
    
    def mark_as_inactive(self, request, queryset):
        """Marque les produits comme inactifs."""
        queryset.update(is_active=False)
        self.message_user(
            request,
            _('%d produits ont été marqués comme inactifs.') % queryset.count()
        )
    mark_as_inactive.short_description = _('Marquer comme inactifs')
    
    def apply_season_promo(self, request, queryset):
        """Applique une promotion saisonnière."""
        queryset.update(
            is_season_promo=True,
            season_promo_discount=20
        )
        msg = _('%d produits ont une promotion saisonnière de 20%%.')
        self.message_user(request, msg % queryset.count())
    apply_season_promo.short_description = _('Appliquer promo saisonnière')