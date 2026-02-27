# -*- coding: utf-8 -*-
"""
Core Invoices Module - Base Models

This module contains the base invoice models.
Invoices are the final step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, F

from core import deferred
from datetime import timedelta


def get_default_expiration_date():
    """Get default expiration date (30 days from now)."""
    return timezone.now() + timedelta(days=30)


class InvoiceStatus:
    """
    Invoice status enumeration.
    
    Workflow: DRAFT -> SENT -> PAID -> OVERDUE -> CANCELLED
               or: DRAFT -> SENT -> PARTIALLY_PAID -> PAID
    """
    DRAFT = 'draft'
    SENT = 'sent'
    PAID = 'paid'
    PARTIALLY_PAID = 'partially_paid'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'
    
    CHOICES = [
        (DRAFT, _('Draft')),
        (SENT, _('Sent')),
        (PAID, _('Paid')),
        (PARTIALLY_PAID, _('Partially Paid')),
        (OVERDUE, _('Overdue')),
        (CANCELLED, _('Cancelled')),
    ]
    
    @classmethod
    def get_default(cls):
        return cls.DRAFT


class BaseInvoiceModel(models.Model):
    """
    Abstract base model for invoices.
    
    An invoice is created from a paid order and represents
    a request for payment.
    """
    
    # Invoice identification
    numero = models.CharField(
        max_length=255, 
        unique=True, 
        editable=False,
        verbose_name=_('Invoice number')
    )
    
    # Customer reference
    customer = deferred.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name=_('Customer')
    )
    
    # Order source
    order_source = deferred.ForeignKey(
        'orders.BaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_('Order source')
    )
    
    # Quote source (optional)
    quote_source = deferred.ForeignKey(
        'quotes.BaseQuote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
        choices=InvoiceStatus.CHOICES,
        default=InvoiceStatus.get_default,
        verbose_name=_('Status')
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Sent at')
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Paid at')
    )
    expiration_date = models.DateTimeField(
        default=get_default_expiration_date,
        verbose_name=_('Expiration date')
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
    paid_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        default=0,
        verbose_name=_('Paid amount')
    )
    
    # Terms and conditions
    invoice_terms = models.TextField(
        blank=True,
        default="NET 30 Days. Finance Charge of 1.5% will be "
                "made on unpaid balances after 30 days.",
        verbose_name=_('Invoice terms')
    )
    
    # Completion flag
    completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed')
    )
    
    class Meta:
        abstract = True
        ordering = ('-created_at',)
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
    
    def __str__(self):
        return f"Invoice {self.numero}"
    
    def generate_number(self, client_pk, invoice_pk):
        """Generate a unique invoice number."""
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        return f"INV-{year}{month}{day}-{client_pk:04d}-{invoice_pk:06d}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            super().save(*args, **kwargs)
            self.numero = self.generate_number(self.customer.pk, self.pk)
            super().save(update_fields=['numero'])
        super().save(*args, **kwargs)
    
    @property
    def due_amount(self):
        """Calculate amount still due."""
        return self.total_amount - self.paid_amount
    
    def is_overdue(self):
        """Check if invoice is overdue."""
        if self.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            return False
        return timezone.now() > self.expiration_date
    
    def is_paid(self):
        """Check if invoice is fully paid."""
        return self.status == InvoiceStatus.PAID
    
    def get_invoice_total(self):
        """Calculate total from items."""
        if self.pk:
            total = self.items.aggregate(
                invoice_total=Sum(F('quantity') * F('price'))
            ).get('invoice_total', 0)
            return total or 0
        return self.total_amount
    
    # Status transition methods
    def send(self):
        """Mark invoice as sent."""
        if self.status == InvoiceStatus.DRAFT:
            self.status = InvoiceStatus.SENT
            self.sent_at = timezone.now()
            self.save()
    
    def record_payment(self, amount, payment_method=''):
        """
        Record a payment against this invoice.
        
        Args:
            amount: Payment amount
            payment_method: Payment method used
        """
        self.paid_amount += amount
        
        if self.paid_amount >= self.total_amount:
            self.status = InvoiceStatus.PAID
            self.paid_at = timezone.now()
            self.completed = True
        else:
            self.status = InvoiceStatus.PARTIALLY_PAID
        
        self.save()
        
        # Create payment record
        from core.payments.models import Payment
        Payment.objects.create(
            invoice=self,
            amount=amount,
            payment_method=payment_method,
            status='completed'
        )
    
    def mark_as_paid(self):
        """Mark invoice as fully paid."""
        self.status = InvoiceStatus.PAID
        self.paid_at = timezone.now()
        self.completed = True
        self.paid_amount = self.total_amount
        self.save()
    
    def mark_as_overdue(self):
        """Mark invoice as overdue."""
        if self.status in [InvoiceStatus.SENT, InvoiceStatus.PARTIALLY_PAID]:
            self.status = InvoiceStatus.OVERDUE
            self.save()
    
    def cancel(self):
        """Cancel the invoice."""
        self.status = InvoiceStatus.CANCELLED
        self.save()
    
    def generate_pdf(self):
        """
        Generate PDF representation of the invoice.
        
        Override in subclass for custom PDF generation.
        """
        raise NotImplementedError(
            "Subclasses must implement generate_pdf()"
        )
    
    def get_items(self):
        """Get all items in the invoice. Override in subclass."""
        return []
    
    def add_item(self, product, quantity, unit_price, tax=0):
        """
        Add an item to the invoice.
        
        Override in subclass.
        """
        raise NotImplementedError(
            "Subclasses must implement add_item()"
        )


class BaseInvoiceItemModel(models.Model):
    """
    Abstract base model for invoice items.
    
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
    
    # Invoice reference
    invoice = models.ForeignKey(
        'BaseInvoiceModel',
        related_name='items',
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
    
    class Meta:
        abstract = True
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')
    
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
BaseInvoice = BaseInvoiceModel
BaseInvoiceItem = BaseInvoiceItemModel


__all__ = [
    'BaseInvoice',
    'BaseInvoiceItem',
    'InvoiceStatus',
    'BaseInvoiceModel',
    'BaseInvoiceItemModel',
    'get_default_expiration_date',
]