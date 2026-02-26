import os
import tempfile
from django.contrib import admin
from core import utils as sh_utils
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from product import models as pro_models
from shop import models as sh_models
from immoshop import models as immo_models 
from core.base_product import models as base_models
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from polymorphic.admin import PolymorphicInlineSupportMixin, StackedPolymorphicInline

class ProductSpecificationValueInline(StackedPolymorphicInline):
    class ImmoSpecificationValueInline(StackedPolymorphicInline.Child):
        model = immo_models.ImmoProductSpecificationValue
    
    model = pro_models.ProductSpecificationValue
    child_inlines = (ImmoSpecificationValueInline, )


# Register your models here.
class ProductImageInline(StackedPolymorphicInline):
    class ImmoProductImageInline(StackedPolymorphicInline.Child):
        model = immo_models.ImmoProductImage
        readonly_fields = ('thumbnail_path', 'large_path',)
        fields = ('title', 'image',  )
        extra = 0
    
    model = pro_models.ProductImage
    child_inlines = ( ImmoProductImageInline,)
    readonly_fields = ('thumbnail_path', 'large_path',)

    
@admin.register(immo_models.ImmoProduct)
class ImmoProductAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    base_model = immo_models.ImmoProduct 
    #inlines = [ImmoProductImageInline,]
    inlines = [ProductSpecificationValueInline, ProductImageInline, ]

    list_display = ['project', 'name', 'slug', 'price', 'stock', 'available', 'created_at', 'updated_at']
    list_filter = ['available', 'created_at', 'updated_at']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    # readonly_fields = ('thumbnail_path', 'large_path',  )
    exlude = ('thumbnail_path', 'large_path',  )
    search_fields = ["title", "slug", ]
    
    fieldsets = (
        (
            "Required Information", {
                # Section Description
                "description" : "Enter the Project information",
                # Group Make and Model
                "fields": (("project", "name"), "slug", "product_code", "description", )
            }, 
        ),
        
        (
            "Required Information 2", {
                "fields": ("stock", "price", "regular_price", "discount_price", )
            },
        ),
        (
            "Additional Information", {
                # Section Description
                #Enable a Collapsible Section
                "classes": ("collapse",), 
                "fields": ("in_stock", "is_active", "default_image")
            }
        )
    )
    
    def save_model(self, request, obj, form, change):
        """
        Custom save method to process images when saving a Product instance.
        """
        super().save_model(request, obj, form, change)
        self.save_form(request, form, change)
        output_dir = os.path.join(settings.MEDIA_ROOT, "images")
        # Check if there are any images associated with this product
        if obj.images.exists():
            # Process each image associated with the product
            for image in obj.images.all():
                # processus de resize images
                thumbnail_path, large_path = sh_utils.process_resize_image(image, output_dir)
                # You can save these paths to the database if needed
                image.large_path = os.path.join("media/images/", os.path.basename(large_path))
                image.thumbnail_path = os.path.join("media/images/", os.path.basename(thumbnail_path))
                image.save() 

    def save_related(self, request, form, formsets, change):
        output_dir = os.path.join(settings.MEDIA_ROOT, "images")
        super().save_related(request, form, formsets, change)

        
        # Accéder à l'instance de Product nouvellement sauvegardée
        product_instance = form.instance
       
        # Modifier les objets ProductImage associés
        for product_image in product_instance.images.all():
            # processus de resize images
            thumbnail_path, large_path = sh_utils.process_resize_image(product_image, output_dir)
            # Faire des modifications sur les objets ProductImage thumbnail_path, large_path = sh_utils.process_resize_image(new_image, output_dir)


            product_image.large_path = os.path.join("/media/images/", os.path.basename(large_path))
            product_image.thumbnail_path = os.path.join("/media/images/", os.path.basename(thumbnail_path))
            product_image.save()


#@admin.register(immo_models.ImmoProductImage)
class ProductImage(admin.ModelAdmin):
    pass
    #list_display =  [field.name for field in immo_models.ImmoProductImage._meta.get_fields()]

class BaseArticleAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        """
        Custom save method to process images when saving a Product instance.
        """
        super().save_model(request, obj, form, change)
        self.save_form(request, form, change)
        output_dir = os.path.join(settings.MEDIA_ROOT, "images")
        # Check if there are any images associated with this product
        if obj.images.exists():
            # Process each image associated with the product
            for image in obj.images.all():
                # processus de resize images
                thumbnail_path, large_path = sh_utils.process_resize_image(image, output_dir)
                # You can save these paths to the database if needed
                image.large_path = os.path.join("media/images/", os.path.basename(large_path))
                image.thumbnail_path = os.path.join("media/images/", os.path.basename(thumbnail_path))
                image.save() 

    def save_related(self, request, form, formsets, change):
        output_dir = os.path.join(settings.MEDIA_ROOT, "images")
        super().save_related(request, form, formsets, change)

        
        # Accéder à l'instance de Product nouvellement sauvegardée
        product_instance = form.instance
       
        # Modifier les objets ProductImage associés
        for product_image in product_instance.images.all():
            # processus de resize images
            thumbnail_path, large_path = sh_utils.process_resize_image(product_image, output_dir)
            # Faire des modifications sur les objets ProductImage thumbnail_path, large_path = sh_utils.process_resize_image(new_image, output_dir)


            product_image.large_path = os.path.join("/media/images/", os.path.basename(large_path))
            product_image.thumbnail_path = os.path.join("/media/images/", os.path.basename(thumbnail_path))
            product_image.save()
