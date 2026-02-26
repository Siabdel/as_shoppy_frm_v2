import os
from django.utils import timezone
from datetime import datetime
import uuid
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.contrib import admin
from polymorphic.admin import PolymorphicInlineSupportMixin
from django.contrib.admin import StackedInline
from django.conf import settings
from core import utils as sh_utils

from product import models as pro_models


class ProductSpecificationInline(admin.TabularInline):
    model = pro_models.ProductSpecification
    extra = 0


class ProductSpecificationValueInline(admin.TabularInline):
    model = pro_models.ProductSpecificationValue
    extra = 0


@admin.register(pro_models.ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    inlines = [ProductSpecificationInline]


@admin.register(pro_models.ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type']
    list_filter = ['product_type']
    search_fields = ['name']


@admin.register(pro_models.ProductSpecificationValue)
class ProductSpecificationValueAdmin(admin.ModelAdmin):
    list_display = ['product', 'specification', 'value']
    list_filter = ['specification']
    search_fields = ['value', 'product__name']


@admin.register(pro_models.ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'product__name']
    readonly_fields = ['thumbnail_path', 'large_path']


class ProductImageInline(StackedInline):
    model = pro_models.ProductImage
    readonly_fields = ('thumbnail_path', 'large_path')
    fields = ('title', 'image')
    extra = 0


class ProductImageAdminMixin:
    """Mixin for handling product image generation."""
    
    def generate_number(self):
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        unique_id = str(uuid.uuid4())[:7].upper()
        new_number = f"PRJ-{year}{month}{day}-{unique_id}"
        return new_number

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'default_image' in form.changed_data:
            self.generate_image_variants(obj)

    def generate_image_variants(self, obj):
        if not obj.default_image:
            return
        original_path = obj.default_image.path
        thumbnail_path = self.get_thumbnail_path(obj)
        self.create_thumbnail(original_path, thumbnail_path)
        obj.thumbnail_path = thumbnail_path

        large_path = self.get_large_path(obj)
        self.create_large_image(original_path, large_path)
        obj.large_path = large_path
        obj.save()

    def get_thumbnail_path(self, obj):
        base, ext = os.path.splitext(obj.default_image.name)
        return f'{base}_thumbnail{ext}'

    def get_large_path(self, obj):
        base, ext = os.path.splitext(obj.default_image.name)
        return f'{base}_large{ext}'

    def create_thumbnail(self, original_path, thumbnail_path):
        with Image.open(original_path) as img:
            img.thumbnail((150, 150))
            base_name = f"thumbnail_150x150_{self.generate_number()}.jpg"
            output_dir = os.path.join(settings.MEDIA_ROOT, "images")
            os.makedirs(output_dir, exist_ok=True)
            full_name = os.path.join(output_dir, base_name)
            img.save(full_name)

    def create_large_image(self, original_path, large_path):
        with Image.open(original_path) as img:
            img.thumbnail((800, 800))
            base_name = f"large_800x800_{self.generate_number()}.jpg"
            output_dir = os.path.join(settings.MEDIA_ROOT, "images")
            os.makedirs(output_dir, exist_ok=True)
            full_name = os.path.join(output_dir, base_name)
            img.save(full_name)

    def save_related(self, request, form, formsets, change):
        output_dir = os.path.join(settings.MEDIA_ROOT, "images")
        os.makedirs(output_dir, exist_ok=True)
        super().save_related(request, form, formsets, change)

        product_instance = form.instance
        for product_image in product_instance.images.all():
            thumbnail_path, large_path = sh_utils.process_resize_image(
                product_image, output_dir
            )
            product_image.large_path = os.path.join(
                "/media/images/", os.path.basename(large_path)
            )
            product_image.thumbnail_path = os.path.join(
                "/media/images/", os.path.basename(thumbnail_path)
            )
            product_image.save()


@admin.register(pro_models.Product)
class ProductAdmin(PolymorphicInlineSupportMixin, ProductImageAdminMixin, admin.ModelAdmin):
    inlines = [ProductSpecificationValueInline, ProductImageInline]
    list_display = [
        'product_code', 'name', 'project', 'category',
        'status', 'price', 'stock', 'available', 
        'in_stock', 'is_active', 'created_at'
    ]
    list_filter = [
        'available', 'in_stock', 'is_active', 
        'status', 'created_at', 'updated_at'
    ]
    list_editable = ['price', 'stock', 'available', 'status']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ["product_code", "name", "slug", "description"]
    readonly_fields = ["product_code", "created_at", "updated_at"]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (
            "Basic Information", {
                "description": "Enter the product information",
                "fields": (
                    ("project", "name"), 
                    ("product_code", "slug", "status"),
                    "category",
                    "description",
                )
            },
        ),
        (
            "Pricing", {
                "fields": (
                    ("price", "regular_price", "discount_price"),
                    ("sales_price", "sales_currency", "max_sales_discount"),
                    "sales_tax",
                ),
            },
        ),
        (
            "Inventory", {
                "fields": (
                    ("stock", "in_stock"),
                    ("available", "is_active"),
                    ("uom", "uos", "uom_to_uos"),
                    ("weight",),
                    ("is_consumable", "is_service"),
                ),
            },
        ),
        (
            "Identifiers", {
                "classes": ("collapse",),
                "fields": (
                    "ean13",
                    ("product_name",),
                ),
            },
        ),
        (
            "Media", {
                "classes": ("collapse",),
                "fields": ("default_image",)
            }
        ),
        (
            "Metadata", {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at")
            }
        ),
    )
