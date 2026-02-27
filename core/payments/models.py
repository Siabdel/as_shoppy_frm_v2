# -*- coding: utf-8 -*-
"""
Core Payments Module - Models

This module contains payment models for tracking:
- Payments against invoices
- Payment transactions
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Payment(models.Model):
    """
    Record of payments made against invoices.
    """
    
    # Invoice reference
    invoice = models.ForeignKey(
        'invoices.BaseInvoice',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Invoice')
    )
    
    # Payment details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Amount')
    )
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('cash', _('Cash')),
            ('check', _('Check')),
            ('bank_transfer', _('Bank Transfer')),
            ('credit_card', _('Credit Card')),
            ('debit_card', _('Debit Card')),
            ('paypal', _('PayPal')),
            ('other', _('Other')),
        ],
        verbose_name=_('Payment method')
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    # Transaction reference
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('Transaction ID')
    )
    
    # Payment date
    payment_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_('Payment date')
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Reference
    reference = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Reference')
    )
    
    class Meta:
        ordering = ('-payment_date',)
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
    
    def __str__(self):
        return f"Payment {self.amount} - {self.invoice.numero}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"PAY-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.pk}"
        super().save(*args, **kwargs)


class PaymentTransaction(models.Model):
    """
    Detailed payment transaction log for debugging and reconciliation.
    """
    
    # Transaction identification
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_('Transaction ID')
    )
    
    # Related objects (optional)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    order = models.ForeignKey(
        'orders.BaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_transactions'
    )
    
    # Transaction details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Amount')
    )
    currency = models.CharField(
        max_length=3,
        default='EUR',
        verbose_name=_('Currency')
    )
    
    # Payment gateway info
    gateway = models.CharField(
        max_length=50,
        verbose_name=_('Payment gateway')
    )
    gateway_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Gateway response')
    )
    
    # Status
    STATUS_CHOICES = [
        ('initiated', _('Initiated')),
        ('processing', _('Processing')),
        ('authorized', _('Authorized')),
        ('captured', _('Captured')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated',
        verbose_name=_('Status')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ('-created_at',)
        verbose_name = _('Payment Transaction')
        verbose_name_plural = _('Payment Transactions')
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.amount} {self.currency}"


__all__ = [
    'Payment',
    'PaymentTransaction',
]