import os
import tempfile
from django.contrib import admin
from core import utils as sh_utils
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from polymorphic.admin import PolymorphicInlineSupportMixin, StackedPolymorphicInline
from product import models as pro_models
from product import admin as pro_admin
from autocar import models as car_models
 
"""
*** VEHICULE AUTO AUTO ***
"""
class AutoSpecificationValueInline(StackedPolymorphicInline):
    class AutoSpecificationValueInline(StackedPolymorphicInline.Child):
        model = car_models.CarProductSpecificationValue
    
    model = pro_models.ProductSpecificationValue
    child_inlines = (AutoSpecificationValueInline, )

# Register your models here.
class CarProductImageInline(StackedPolymorphicInline):
    class AutoProductImageInline(StackedPolymorphicInline.Child):
        model = car_models.CarProductImage
        readonly_fields = ('thumbnail_path', 'large_path',)
        fields = ('title', 'image',  )
        extra = 0
    
    model = pro_models.ProductImage
    child_inlines = ( AutoProductImageInline,)
    readonly_fields = ('thumbnail_path', 'large_path',)

@admin.register(car_models.VehiculeProduct)
class AutoAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    #base_model = car_models.VehiculeProduct 
    inlines = [AutoSpecificationValueInline, CarProductImageInline, ]
    list_display = ['project', 'name', 'slug', 'price', 'stock', 'available', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',), }
    
admin.register(car_models.VehiculeProduct, AutoAdmin)