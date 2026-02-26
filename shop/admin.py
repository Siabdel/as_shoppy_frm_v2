import os
import tempfile
from django.contrib import admin
from shop import models as sh_models

@admin.register(sh_models.ShopCart)
class ShopCartAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_cart', 'created_at', ]
    
    def get_cart(self, obj):
        return obj.id


@admin.register(sh_models.CartItem)
class CartItemAdmin(admin.ModelAdmin):
    #list_display =  [field.name for field in sh_models.CartItem._meta.get_fields()]
    list_display =  ['product', ]