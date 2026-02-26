# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Invoice, InvoiceItem


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'client',
        'invoice_total',
        'create_by',
        'create_at',
        'expiration_date',
        'total_amount',
        'status',
        'invoice_terms',
    )
    list_filter = ('client', 'create_by', 'create_at', 'expiration_date')


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'invoice',
        'product',
        'quantity',
        'price',
        'rate',
        'tax',
    )
    list_filter = ('invoice',)
