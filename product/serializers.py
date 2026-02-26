# product/serializers.py

from rest_framework import serializers
from .models import (
    Product, ProductImage, ProductType, 
    ProductSpecification, ProductSpecificationValue
)
from project.models import Project
from core.taxonomy.models import MPCategory


class MPCategorySerializer(serializers.ModelSerializer):
    """Serializer for product category."""
    
    class Meta:
        model = MPCategory
        fields = ['id', 'name', 'slug']


class ProjectBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for project reference."""
    
    class Meta:
        model = Project
        fields = ['id', 'code', 'name', 'slug']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'title', 'slug', 'image', 'image_url',
            'thumbnail_path', 'large_path', 'created_at'
        ]
    
    def get_image_url(self, obj):
        """Get absolute URL for the image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for product specifications."""
    
    class Meta:
        model = ProductSpecification
        fields = ['id', 'product_type', 'name']


class ProductSpecificationValueSerializer(serializers.ModelSerializer):
    """Serializer for product specification values."""
    specification_name = serializers.CharField(
        source='specification.name', read_only=True
    )
    
    class Meta:
        model = ProductSpecificationValue
        fields = ['id', 'specification', 'specification_name', 'value']


class ProductTypeSerializer(serializers.ModelSerializer):
    """Serializer for product types."""
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductType
        fields = ['id', 'name', 'is_active', 'specifications']


class ProductListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for product list views.
    """
    category = MPCategorySerializer(read_only=True)
    project = ProjectBriefSerializer(read_only=True)
    default_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'name', 'slug', 
            'default_image', 'default_image_url',
            'price', 'available', 'in_stock',
            'category', 'project', 'status'
        ]
    
    def get_default_image_url(self, obj):
        """Get URL for default image."""
        if obj.default_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.default_image.url)
            return obj.default_image.url
        return None


class ProductSerializer(serializers.ModelSerializer):
    """
    Full serializer for Product model.
    """
    category = MPCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=MPCategory.objects.all(), 
        source='category', 
        write_only=True, 
        required=False, 
        allow_null=True
    )
    project = ProjectBriefSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    specification_values = ProductSpecificationValueSerializer(
        many=True, read_only=True, source='productspecificationvalue_set'
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'category', 'category_id',
            'name', 'slug', 'description', 
            'price', 'regular_price', 'discount_price',
            'available', 'stock', 'in_stock', 'is_active',
            'created_at', 'updated_at', 'default_image',
            'project', 'project_id', 'product_name', 
            'status', 'status_display',
            'ean13', 'uom', 'uos', 'uom_to_uos', 'weight',
            'is_consumable', 'is_service', 'sales_price',
            'sales_currency', 'max_sales_discount', 'sales_tax',
            'images', 'specification_values'
        ]
        read_only_fields = [
            'slug', 'created_at', 'updated_at', 'product_code'
        ]

    def create(self, validated_data):
        """Create a new product."""
        return Product.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing product."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating products.
    """
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=MPCategory.objects.all(), 
        source='category', 
        required=False, 
        allow_null=True
    )
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project'
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'category_id', 'project_id',
            'price', 'regular_price', 'discount_price',
            'stock', 'available', 'in_stock', 'is_active',
            'default_image', 'product_name', 'status',
            'ean13', 'uom', 'uos', 'uom_to_uos', 'weight',
            'is_consumable', 'is_service', 'sales_price',
            'sales_currency', 'max_sales_discount', 'sales_tax'
        ]
