"""
CMagic Sport - Enhanced Django Admin Configuration
Professional admin interface for managing the basketball shoes e-commerce store
"""

from django.contrib import admin
from django.utils.html import format_html
from polymorphic.admin import PolymorphicInlineSupportMixin
from django.contrib.admin import StackedInline, TabularInline

from product import models as pro_models
from product.admin import ProductSpecificationInline


# Custom Admin Site Configuration for CMagic Sport
class CMagicAdminSite(admin.AdminSite):
    site_header = "CMagic Sport Administration"
    site_title = "CMagic Sport E-Commerce"
    index_title = "Store Management Dashboard"
    
    def each_context(self, request):
        context = super().each_context(request)
        context.update({
            'cmagic_brand': 'CMagic Sport',
            'cmagic_stats': {
                'total_products': pro_models.Product.objects.count(),
                'active_products': pro_models.Product.objects.filter(is_active=True).count(),
                'low_stock': pro_models.Product.objects.filter(stock__lt=10, stock__gt=0).count(),
                'out_of_stock': pro_models.Product.objects.filter(stock=0).count(),
            }
        })
        return context


cmagic_admin_site = CMagicAdminSite(name='cmagic_admin')


# Inlines
class ProductSpecificationValueInline(TabularInline):
    model = pro_models.ProductSpecificationValue
    extra = 0
    fields = ('specification', 'value')
    autocomplete_fields = ['specification']


class ProductImageInline(StackedInline):
    model = pro_models.ProductImage
    extra = 0
    fields = ('title', 'image', 'is_primary')
    readonly_fields = ('thumbnail_path',)


# Product Admin with Enhanced Features
@admin.register(pro_models.Product)
class ProductAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    # Inlines
    inlines = [ProductSpecificationValueInline, ProductImageInline]
    
    # List Display
    list_display = [
        'product_code', 
        'product_image_preview',
        'name', 
        'category_display',
        'status_badge',
        'price_display',
        'stock_status',
        'available_toggle',
        'created_at'
    ]
    
    # List Filter
    list_filter = [
        'available', 
        'in_stock', 
        'is_active', 
        'status', 
        'category',
        'created_at', 
        'updated_at'
    ]
    
    # List Editable
    list_editable = ['available', 'status']
    
    # Search Fields
    search_fields = ['product_code', 'name', 'slug', 'description']
    
    # Readonly Fields
    readonly_fields = ['product_code', 'created_at', 'updated_at']
    
    # Prepopulated Fields
    prepopulated_fields = {'slug': ('name',)}
    
    # Date Hierarchy
    date_hierarchy = 'created_at'
    
    # Ordering
    ordering = ['-created_at']
    
    # Fieldsets for organized form display
    fieldsets = (
        ("Basic Information", {
            'description': 'Enter the basic product information',
            'fields': (
                'project',
                'category',
                'name',
                'slug',
                'description',
            )
        }),
        ("Pricing", {
            'description': 'Set product pricing',
            'fields': (
                'price',
                'regular_price',
                'discount_price',
            )
        }),
        ("Inventory", {
            'description': 'Manage stock and availability',
            'fields': (
                'stock',
                'available',
                'in_stock',
                'status',
            )
        }),
        ("Product Code", {
            'classes': ('collapse',),
            'fields': ('product_code',)
        }),
        ("Media", {
            'classes': ('collapse',),
            'fields': ('default_image',)
        }),
        ("Additional Info", {
            'classes': ('collapse',),
            'fields': (
                'is_active',
                'ean13',
                'weight',
                'uom',
            )
        }),
    )
    
    # Custom Methods
    def product_image_preview(self, obj):
        if obj.default_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;">',
                obj.default_image.url
            )
        return format_html('<span class="text-muted">No Image</span>')
    product_image_preview.short_description = 'Image'
    
    def category_display(self, obj):
        if obj.category:
            return obj.category.name
        return '-'
    category_display.short_description = 'Category'
    
    def status_badge(self, obj):
        colors = {
            'AVL': 'success',
            'RSV': 'warning',
            'SLD': 'info',
            'PND': 'secondary',
            'UNV': 'danger',
            'CMS': 'primary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def price_display(self, obj):
        if obj.regular_price and obj.regular_price > obj.price:
            return format_html(
                '<span class="text-danger text-decoration-line-through">${}</span> '
                '<span class="text-success fw-bold">${}</span>',
                obj.regular_price,
                obj.price
            )
        return format_html('<span class="fw-bold">${}</span>', obj.price)
    price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span class="badge bg-danger">Out of Stock</span>')
        elif obj.stock < 10:
            return format_html('<span class="badge bg-warning text-dark">Low Stock ({})</span>', obj.stock)
        else:
            return format_html('<span class="badge bg-success">In Stock ({})</span>', obj.stock)
    stock_status.short_description = 'Stock'
    
    def available_toggle(self, obj):
        if obj.available:
            return format_html('<span class="text-success"><i class="bi bi-check-circle-fill"></i> Yes</span>')
        return format_html('<span class="text-danger"><i class="bi bi-x-circle-fill"></i> No</span>')
    available_toggle.short_description = 'Available'


# Product Type Admin
@admin.register(pro_models.ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'specification_count']
    list_filter = ['is_active']
    search_fields = ['name']
    inlines = [ProductSpecificationInline]
    
    def specification_count(self, obj):
        return obj.specifications.count()
    specification_count.short_description = 'Specifications'


# Product Specification Admin
class ProductSpecificationInline(admin.TabularInline):
    model = pro_models.ProductSpecification
    extra = 0
    fields = ('name',)


@admin.register(pro_models.ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type']
    list_filter = ['product_type']
    search_fields = ['name']


@admin.register(pro_models.ProductSpecificationValue)
class ProductSpecificationValueAdmin(admin.ModelAdmin):
    list_display = ['product', 'specification', 'value']
    list_filter = ['specification', 'product__category']
    search_fields = ['value', 'product__name']
    autocomplete_fields = ['product', 'specification']


# Product Image Admin
@admin.register(pro_models.ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'product', 'is_primary', 'created_at']
    list_filter = ['created_at', 'product__category']
    search_fields = ['title', 'product__name']
    readonly_fields = ('thumbnail_path', 'large_path')
    fields = ('title', 'product', 'image', 'is_primary')


# Custom CSS for Admin
class CMagicAdminUtils:
    """Utilities for enhancing admin appearance"""
    
    @staticmethod
    def get_admin_styles():
        return """
        <style>
        /* CMagic Sport Admin Custom Styles */
        .cmagic-header {
            background: linear-gradient(135deg, #ff6b35 0%, #e55a2b 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .cmagic-stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .cmagic-stat-card {
            flex: 1;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .cmagic-stat-card h3 {
            margin: 0;
            color: #ff6b35;
            font-size: 2rem;
        }
        
        .cmagic-stat-card p {
            margin: 0;
            color: #666;
        }
        
        /* Badge improvements */
        .badge-status {
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: 500;
        }
        
        /* Table improvements */
        .model-product .field-product_image_preview {
            width: 60px;
        }
        
        .model-product .field-price_display {
            min-width: 100px;
        }
        
        /* Form improvements */
        .form-row {
            padding: 10px;
            border-radius: 5px;
        }
        
        /* Sidebar improvements */
        #cmagic-sidebar {
            background: #1a1a2e;
            color: white;
        }
        
        .module h3, .module caption {
            background: #ff6b35;
        }
        </style>
        """


# Export admin configuration to main admin
__all__ = [
    'ProductAdmin',
    'ProductTypeAdmin', 
    'ProductSpecificationAdmin',
    'ProductSpecificationValueAdmin',
    'ProductImageAdmin',
    'cmagic_admin_site',
    'CMagicAdminUtils',
]