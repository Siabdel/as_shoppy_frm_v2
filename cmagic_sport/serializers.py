# -*- coding: utf-8 -*-
"""
Serializers DRF pour CMagic Sport.
"""
from rest_framework import serializers
from .models import SportProduct


class SportProductSerializer(serializers.ModelSerializer):
    """
    Serializer pour les produits sport.
    """
    
    # Champs calculés
    current_price = serializers.SerializerMethodField()
    brand_display = serializers.CharField(
        source='get_brand_display',
        read_only=True
    )
    product_type_display = serializers.CharField(
        source='get_product_type_display',
        read_only=True
    )
    material_display = serializers.CharField(
        source='get_material_display',
        read_only=True
    )
    gender_display = serializers.CharField(
        source='get_gender_display',
        read_only=True
    )
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
            'detailed_description',
            # Informations produit
            'brand',
            'brand_display',
            'product_type',
            'product_type_display',
            'model_name',
            'color',
            'color_secondary',
            'colorway',
            'material',
            'material_display',
            'gender',
            'gender_display',
            # Tailles
            'size_eu',
            'size_us',
            'size_uk',
            'size_display',
            # Référence
            'style_code',
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
            # Technologies
            'technologies',
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
    brand_display = serializers.CharField(
        source='get_brand_display',
        read_only=True
    )
    
    class Meta:
        model = SportProduct
        fields = [
            'id',
            'name',
            'slug',
            'brand',
            'brand_display',
            'color',
            'colorway',
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
            'detailed_description',
            'category',
            # Informations produit
            'brand',
            'product_type',
            'model_name',
            'color',
            'color_secondary',
            'colorway',
            'material',
            'gender',
            # Tailles
            'size_eu',
            'size_us',
            'size_uk',
            # Référence
            'style_code',
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
            # Technologies
            'technologies',
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