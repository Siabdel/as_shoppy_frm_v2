"""
ImmoProduct Serializers

Django REST Framework serializers for the real estate product API.
"""
from rest_framework import serializers

from .models import ImmoProduct
from product.models import ProductImage
from project.models import Project
from core.taxonomy.models import MPCategory


class ProjectSerializer(serializers.ModelSerializer):
    """Simplified Project serializer for nesting."""
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'slug']


class MPCategorySerializer(serializers.ModelSerializer):
    """Simplified Category serializer for nesting."""
    
    class Meta:
        model = MPCategory
        fields = ['id', 'name']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images."""
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'title', 'slug', 'image_url', 'thumbnail_url', 'created_at']
    
    def get_image_url(self, obj):
        """Return absolute URL for image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Return thumbnail URL if available."""
        if hasattr(obj, 'thumbnail_path') and obj.thumbnail_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail_path)
            return obj.thumbnail_path
        return None


class ImmoProductSerializer(serializers.ModelSerializer):
    """
    Serializer for ImmoProduct model.
    
    Provides full product details including related objects.
    """
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        source='project',
        write_only=True
    )
    category = MPCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=MPCategory.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    images = ProductImageSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ImmoProduct
        fields = [
            'id', 'product_name', 'name', 'slug', 'description',
            'project', 'project_id', 'category', 'category_id',
            'price', 'regular_price', 'discount_price',
            'available', 'stock', 'in_stock', 'status', 'status_display',
            'product_code', 'default_image', 'images',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'product_code', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new immo product."""
        return ImmoProduct.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing immo product."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ImmoProductListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for product list views.
    
    Provides essential information for list displays.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    default_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImmoProduct
        fields = [
            'id', 'product_name', 'name', 'slug',
            'project_name', 'category_name',
            'price', 'available', 'status', 'status_display',
            'default_image_url', 'created_at'
        ]
    
    def get_default_image_url(self, obj):
        """Return default image URL if available."""
        if obj.default_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.default_image)
            return obj.default_image
        return None
