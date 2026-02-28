# -*- coding: utf-8 -*-
"""
Serializers DRF pour CMagic Sport.
"""
from rest_framework import serializers
from .models import SportProduct, Order, OrderItem


class SportProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour les produits sport.
    """
    
    # Champs calculés
    current_price = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    color_secondary = serializers.SerializerMethodField()
    colorway = serializers.SerializerMethodField()
    material = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    size_eu = serializers.SerializerMethodField()
    size_us = serializers.SerializerMethodField()
    size_uk = serializers.SerializerMethodField()
    style_code = serializers.SerializerMethodField()
    size_display = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    absolute_url = serializers.CharField(
        source='get_absolute_url',
        read_only=True
    )
    
    class Meta:
        model = SportProduct
        fields = [
            'id',
            'name',
            'slug',
            'description',
            # Informations produit
            'product_type',
            # Tailles
            'available_sizes',
            'size_display',
            # Référence
            'product_code',
            'ean13',
            # Prix
            'price',
            'regular_price',
            'discount_price',
            'current_price',
            # Promo
            'is_season_promo',
            'season_promo_discount',
            # Stock
            'stock',
            'in_stock',
            'available',
            'availability',
            # Collection
            'collection_year',
            'is_limited_edition',
            # Média
            'default_image',
            # Métadonnées
            'absolute_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'product_code',
            'created_at',
            'updated_at',
        ]
    
    def get_current_price(self, obj):
        """Retourne le prix actuel avec les promotions."""
        return float(obj.get_price())
    
    def get_brand(self, obj):
        return obj.get_brand()
    
    def get_model_name(self, obj):
        return obj.get_model()
    
    def get_color(self, obj):
        return obj.get_color()
    
    def get_color_secondary(self, obj):
        return None
    
    def get_colorway(self, obj):
        return None
    
    def get_material(self, obj):
        return obj.get_material()
    
    def get_gender(self, obj):
        return obj.get_gender()
    
    def get_size_eu(self, obj):
        return obj.get_size()
    
    def get_size_us(self, obj):
        return None
    
    def get_size_uk(self, obj):
        return None
    
    def get_style_code(self, obj):
        return obj.get_style_code()
    
    def get_size_display(self, obj):
        """Retourne l'affichage des tailles."""
        return obj.get_size_display()
    
    def get_availability(self, obj):
        """Retourne les informations de disponibilité."""
        availability = obj.get_availability()
        return {
            'is_available': availability.is_available,
            'quantity': availability.quantity,
            'message': availability.message,
        }


class SportProductListSerializer(serializers.ModelSerializer):
    """
    Serializer simplifié pour les listes de produits.
    """
    
    current_price = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    
    class Meta:
        model = SportProduct
        fields = [
            'id',
            'name',
            'slug',
            'brand',
            'color',
            'price',
            'current_price',
            'stock',
            'in_stock',
            'default_image',
            'is_limited_edition',
            'is_season_promo',
        ]
    
    def get_current_price(self, obj):
        """Retourne le prix actuel avec les promotions."""
        return float(obj.get_price())
    
    def get_brand(self, obj):
        """Retourne la marque via les spécifications."""
        return obj.get_brand()
    
    def get_color(self, obj):
        """Retourne la couleur via les spécifications."""
        return obj.get_color()


class SportProductCreateSerializer(serializers.ModelSerializer):
    """
    Serializer pour la création de produits sport.
    """
    
    class Meta:
        model = SportProduct
        fields = [
            'name',
            'slug',
            'description',
            'category',
            # Informations produit
            'product_type',
            # Tailles
            'available_sizes',
            # Référence
            'ean13',
            # Prix
            'price',
            'regular_price',
            'discount_price',
            # Promo
            'is_season_promo',
            'season_promo_discount',
            # Stock
            'stock',
            'in_stock',
            'available',
            # Collection
            'collection_year',
            'is_limited_edition',
            # Média
            'default_image',
        ]
    
    def create(self, validated_data):
        """Création du produit avec génération du slug si absent."""
        from django.utils.text import slugify
        import uuid
        
        if not validated_data.get('slug'):
            # Générer un slug unique
            base_slug = slugify(validated_data['name'])
            validated_data['slug'] = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        
        return super().create(validated_data)


# ============================================
# Serializers pour les Commandes
# ============================================

class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer pour les éléments de commande."""
    
    total_price = serializers.DecimalField(
        source='total_price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_sku',
            'product_size',
            'product_color',
            'product_brand',
            'unit_price',
            'quantity',
            'total_price',
            'product_image',
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer pour la liste des commandes (vue resumee).
    """
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    items_count = serializers.SerializerMethodField()
    total_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'created_at',
            'total',
            'total_formatted',
            'items_count',
            'tracking_number',
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_total_formatted(self, obj):
        return f"{obj.total} €"


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer pour le detail d'une commande (vue complete).
    """
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    items = OrderItemSerializer(many=True, read_only=True)
    status_progress = serializers.SerializerMethodField()
    subtotal_formatted = serializers.SerializerMethodField()
    shipping_cost_formatted = serializers.SerializerMethodField()
    tax_amount_formatted = serializers.SerializerMethodField()
    total_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'status',
            'status_display',
            'status_progress',
            # Informations client
            'first_name',
            'last_name',
            'email',
            'phone',
            # Adresse
            'shipping_address',
            'shipping_city',
            'shipping_postal_code',
            'shipping_country',
            # Suivi
            'tracking_number',
            'tracking_url',
            'carrier',
            # Dates
            'created_at',
            'updated_at',
            'shipped_at',
            'delivered_at',
            # Montants
            'subtotal',
            'subtotal_formatted',
            'shipping_cost',
            'shipping_cost_formatted',
            'tax_amount',
            'tax_amount_formatted',
            'total',
            'total_formatted',
            # Notes
            'notes',
            # Items
            'items',
        ]
    
    def get_status_progress(self, obj):
        return obj.get_status_progress()
    
    def get_subtotal_formatted(self, obj):
        return f"{obj.subtotal} €"
    
    def get_shipping_cost_formatted(self, obj):
        return f"{obj.shipping_cost} €"
    
    def get_tax_amount_formatted(self, obj):
        return f"{obj.tax_amount} €"
    
    def get_total_formatted(self, obj):
        return f"{obj.total} €"