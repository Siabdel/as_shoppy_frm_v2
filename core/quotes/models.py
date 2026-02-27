# -*- coding: utf-8 -*-
"""
Core Quotes Module - Base Models

This module contains the base quote (devis) models.
Quotes are the second step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

from core import deferred


class QuoteStatus:
    """
    Quote status enumeration.
    
    Workflow: DRAFT -> SENT -> ACCEPTED/REJECTED/EXPIRED -> CONVERTED
    """
    DRAFT = 'draft'
    SENT = 'sent'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    EXPIRED = 'expired'
    CONVERTED = 'converted'
    
    CHOICES = [
        (DRAFT, _('Draft')),
        (SENT, _('Sent')),
        (ACCEPTED, _('Accepted')),
        (REJECTED, _('Rejected')),
        (EXPIRED, _('Expired')),
        (CONVERTED, _('Converted to Order')),
    ]
    
    @classmethod
    def get_default(cls):
        return cls.DRAFT


class BaseQuoteModel(models.Model):
    """
    Abstract base model for quotes (devis).
    
    A quote is a formal proposal sent to a customer with:
    - List of products and quantities
    - Prices (fixed at time of quote creation)
    - Validity period (expiration date)
    - Status (draft, sent, accepted, rejected, expired, converted)
    """
    
    # Quote identification
    numero = models.CharField(
        max_length=255, 
        unique=True, 
        editable=False,
        verbose_name=_('Quote number')
    )
    
    # Customer reference
    customer = deferred.ForeignKey(
        'customer.Customer',
        on_delete=models.CASCADE,
        related_name='quotes',
        verbose_name=_('Customer')
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
        choices=QuoteStatus.CHOICES,
        default=QuoteStatus.get_default,
        verbose_name=_('Status')
    )
    
    # Dates
    created_at = models.DateField(auto_now_add=True)
    expiration_date = models.DateField(
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
    
    # Terms and conditions
    quote_terms = models.TextField(
        blank=True,
        verbose_name=_('Quote terms')
    )
    
    # Completion flag
    completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed')
    )
    
    class Meta:
        abstract = True
        ordering = ('-created_at',)
        verbose_name = _('Quote')
        verbose_name_plural = _('Quotes')
    
    def __str__(self):
        return f"Quote {self.numero}"
    
    def generate_number(self, client_pk, quote_pk):
        """Generate a unique quote number."""
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        return f"QUO-{year}{month}{day}-{client_pk:04d}-{quote_pk:06d}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            super().save(*args, **kwargs)
            self.numero = self.generate_number(self.customer.pk, self.pk)
            super().save(update_fields=['numero'])
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the quote has expired."""
        return timezone.now().date() > self.expiration_date
    
    def is_valid_for_conversion(self):
        """Check if quote can be converted to order."""
        return (
            self.status == QuoteStatus.ACCEPTED and 
            not self.is_expired() and
            not self.status == QuoteStatus.CONVERTED
        )
    
    # Status transition methods
    def mark_as_sent(self):
        """Mark quote as sent."""
        if self.status == QuoteStatus.DRAFT:
            self.status = QuoteStatus.SENT
            self.save()
    
    def mark_as_accepted(self):
        """Mark quote as accepted."""
        if self.status == QuoteStatus.SENT:
            self.status = QuoteStatus.ACCEPTED
            self.save()
    
    def mark_as_rejected(self):
        """Mark quote as rejected."""
        if self.status == QuoteStatus.SENT:
            self.status = QuoteStatus.REJECTED
            self.save()
    
    def mark_as_expired(self):
        """Mark quote as expired."""
        if self.status in [QuoteStatus.DRAFT, QuoteStatus.SENT]:
            self.status = QuoteStatus.EXPIRED
            self.save()
    
    def to_order(self, request):
        """
        Convert quote to order.
        
        This is the Quote -> Order step in the workflow.
        
        Args:
            request: HTTP request
            
        Returns:
            Order: The created order
            
        Raises:
            ValueError: If quote is not valid for conversion
        """
        if not self.is_valid_for_conversion():
            raise ValueError(
                _("Only accepted quotes that are not expired can be converted to orders.")
            )
        
        # Import here to avoid circular imports
        from core.orders.models import BaseOrderModel
        
        order = BaseOrderModel.objects.create(
            customer=self.customer,
            created_by=request.user,
            quote_source=self,
            total_amount=self.total_amount,
            status='created',  # OrderStatus.CREATED
        )
        
        # Copy items from quote to order
        for quote_item in self.get_items():
            order.add_item(
                product=quote_item.product,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
            )
        
        # Update quote status
        self.status = QuoteStatus.CONVERTED
        self.save()
        
        return order
    
    def get_items(self):
        """Get all items in the quote. Override in subclass."""
        return []


class BaseQuoteItemModel(models.Model):
    """
    Abstract base model for quote items.
    
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
    
    # Quote reference
    quote = models.ForeignKey(
        'BaseQuoteModel',
        related_name='quote_items',
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
        verbose_name = _('Quote Item')
        verbose_name_plural = _('Quote Items')
    
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
BaseQuote = BaseQuoteModel
BaseQuoteItem = BaseQuoteItemModel


__all__ = [
    'BaseQuote',
    'BaseQuoteItem',
    'QuoteStatus',
    'BaseQuoteModel',
    'BaseQuoteItemModel',
]