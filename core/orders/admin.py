from django.contrib import admin
# Abstract models cannot be registered with admin
# They should be extended by business-specific apps that provide concrete implementations

# from .models import BaseOrderModel as Order, BaseOrderItemModel as OrderItem


# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     raw_id_fields = ['product']


# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ['id', 'first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'paid', 'created',
#                     'updated']
#     list_filter = ['paid', 'created', 'updated']
#     inlines = [OrderItemInline]


