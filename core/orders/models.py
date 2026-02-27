# -*- coding: utf-8 -*-
"""
Core Orders Module - Base Models

This module contains the base order models.
Orders are the third step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice

Stock Management:
- Reservation: At order time (reserve stock for the order)
- Decrement: On delivery (permanent reduction in inventory)
- History: All stock movements are tracked
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from core import deferred


class OrderStatus:
    """
    Order status enumeration.
    
    Workflow: CREATED -> AWAITING_PAYMENT -> PAID -> SHIPPED -> COMPLETED
               or: CREATED -> AWAITING_PAYMENT -> CANCELLED
    """
    CREATED = 'created'
    AWAITING_PAYMENT = 'awaiting_payment'
    PAID = 'paid'
    SHIPPED = 'shipped'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    CHOICES = [
        (CREATED, _('Created')),
        (AWAITING_PAYMENT, _('Awaiting Payment')),
        (PAID, _('Paid')),
        (SHIPPED, _('Shipped')),
        (COMPLETED, _('Completed')),
        (CANCELLED, _('Cancelled')),
    ]
    
    @classmethod
    def get_default(cls):
        return cls.CREATED


class BaseOrderModel(models.Model):
    """
    Abstract base model for orders.
    
    An order is created from an accepted quote and represents
    a confirmed transaction.
    """
    
    # Order identification
    numero = models.CharField(
        max_length=255, 
        unique=True, 
        editable=False,
        verbose_name=_('Order number')
    )
    
    # Customer reference
    customer = deferred.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('Customer')
    )
    
    # Quote source (optional - orders can be created directly)
    quote_source = deferred.ForeignKey(
        'quotes.BaseQuote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_orders',
        verbose_name=_('Quote source')
    )
    
    # Creator
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name=_('Created by')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.CHOICES,
        default=OrderStatus.get_default,
        verbose_name=_('Status')
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Paid at')
    )
    shipped_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Shipped at')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed at')
    )
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Cancelled at')
    )
    
    # Totals
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name=_('Total amount')
    )
    tax_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name=_('Tax amount')
    )
    shipping_cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        verbose_name=_('Shipping cost')
    )
    
    # Completion flag
    completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed')
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    class Meta:
        abstract = True
        ordering = ('-created_at',)
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
    
    def __str__(self):
        return f"Order {self.numero}"
    
    def generate_number(self, order_pk):
        """Generate a unique order number."""
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        return f"ORD-{year}{month}{day}-{order_pk:06d}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            super().save(*args, **kwargs)
            self.numero = self.generate_number(self.pk)
            super().save(update_fields=['numero'])
        super().save(*args, **kwargs)
    
    def is_paid(self):
        """Check if order has been paid."""
        return self.status in [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.COMPLETED]
    
    def is_cancelled(self):
        """Check if order has been cancelled."""
        return self.status == OrderStatus.CANCELLED
    
    def is_completed(self):
        """Check if order has been completed."""
        return self.status == OrderStatus.COMPLETED
    
    # Status transition methods
    def mark_as_paid(self):
        """Mark order as paid and reserve stock."""
        if self.status == OrderStatus.AWAITING_PAYMENT:
            self.status = OrderStatus.PAID
            self.paid_at = timezone.now()
            self.save()
            self.reserve_stock()
    
    def mark_as_shipped(self):
        """Mark order as shipped and decrement stock."""
        if self.status == OrderStatus.PAID:
            self.status = OrderStatus.SHIPPED
            self.shipped_at = timezone.now()
            self.save()
            self.decrement_stock()
    
    def mark_as_completed(self):
        """Mark order as completed."""
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.COMPLETED
            self.completed_at = timezone.now()
            self.completed = True
            self.save()
    
    def mark_as_cancelled(self):
        """Mark order as cancelled and release stock."""
        if self.status not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            self.status = OrderStatus.CANCELLED
            self.cancelled_at = timezone.now()
            self.save()
            self.release_stock()
    
    def reserve_stock(self):
        """
        Reserve stock for all items in the order.
        
        Called when order is paid.
        """
        for item in self.get_items():
            if item.product.managed_availability():
                item.product.reserve_stock(item.quantity, self.numero)
    
    def release_stock(self):
        """
        Release reserved stock.
        
        Called when order is cancelled.
        """
        for item in self.get_items():
            if item.product.managed_availability():
                item.product.release_reservation(item.quantity, self.numero)
    
    def decrement_stock(self):
        """
        Permanently decrement stock for all items.
        
        Called when order is shipped/delivered.
        """
        for item in self.get_items():
            if item.product.managed_availability():
                item.product.decrement_stock(item.quantity, 'sale')
    
    def to_invoice(self, request):
        """
        Convert order to invoice.
        
        This is the Order -> Invoice step in the workflow.
        
        Args:
            request: HTTP request
            
        Returns:
            Invoice: The created invoice
        """
        from core.invoices.models import BaseInvoiceModel
        
        invoice = BaseInvoiceModel.objects.create(
            customer=self.customer,
            created_by=request.user,
            order_source=self,
            total_amount=self.total_amount,
            status='draft',  # InvoiceStatus.DRAFT
        )
        
        # Copy items from order to invoice
        for order_item in self.get_items():
            invoice.add_item(
                product=order_item.product,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
            )
        
        return invoice
    
    def get_items(self):
        """Get all items in the order. Override in subclass."""
        return []


class BaseOrderItemModel(models.Model):
    """
    Abstract base model for order items.
    
    Uses ContentTypes to support polymorphic product relations.
    """
    
    # Polymorphic product reference
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__startswith': 'product'},
    )
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    
    # Order reference
    order = models.ForeignKey(
        'BaseOrderModel',
        related_name='order_items',
        on_delete=models.CASCADE
    )
    
    # Item fields
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_('Discount rate (%)')
    )
    tax = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0,
        verbose_name=_('Tax rate (%)')
    )
    
    # Stock tracking
    is_reserved = models.BooleanField(default=False)
    is_shipped = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
    
    @property
    def subtotal(self):
        """Calculate subtotal without tax."""
        return self.quantity * self.unit_price
    
    @property
    def subtotal_with_tax(self):
        """Calculate subtotal with tax."""
        tax_amount = self.subtotal * (self.tax / 100)
        return self.subtotal + tax_amount
    
    def __str__(self):
        return f"{self.product} - {self.subtotal}"


# Aliases for backward compatibility
BaseOrder = BaseOrderModel
BaseOrderItem = BaseOrderItemModel


__all__ = [
    'BaseOrder',
    'BaseOrderItem',
    'OrderStatus',
    'BaseOrderModel',
    'BaseOrderItemModel',
]
