# -*- coding: utf-8 -*-
"""
Invoice Interfaces - Abstract Base Classes for Invoice Management

This module defines the contracts for invoice operations.
The invoice is the final step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from decimal import Decimal
from django.http import HttpRequest
from datetime import datetime


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
        (DRAFT, 'Draft'),
        (SENT, 'Sent'),
        (PAID, 'Paid'),
        (PARTIALLY_PAID, 'Partially Paid'),
        (OVERDUE, 'Overdue'),
        (CANCELLED, 'Cancelled'),
    ]


class InvoiceItemInterface(ABC):
    """
    Abstract base class for invoice item behavior.
    """
    
    @property
    @abstractmethod
    def product(self) -> Any:
        """Return the product associated with this invoice item."""
        pass
    
    @property
    @abstractmethod
    def quantity(self) -> int:
        """Return the quantity of the product."""
        pass
    
    @property
    @abstractmethod
    def unit_price(self) -> Decimal:
        """Return the unit price at time of invoice creation."""
        pass
    
    @property
    @abstractmethod
    def tax_rate(self) -> Decimal:
        """Return the tax rate applied to this item."""
        pass
    
    @property
    @abstractmethod
    def total_price(self) -> Decimal:
        """Return the total price (quantity * unit_price)."""
        pass
    
    @property
    @abstractmethod
    def total_price_with_tax(self) -> Decimal:
        """Return the total price including tax."""
        pass


class InvoiceInterface(ABC):
    """
    Abstract base class for invoice behavior.
    
    An invoice is created from a paid order and represents
    a request for payment. It goes through several status
    transitions until payment is received.
    
    Workflow: Order -> Invoice
    
    The invoice is the final document in the business workflow.
    """
    
    @property
    @abstractmethod
    def invoice_number(self) -> str:
        """Return the unique invoice number."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Return the current status of the invoice."""
        pass
    
    @property
    @abstractmethod
    def customer(self) -> Any:
        """Return the customer associated with this invoice."""
        pass
    
    @property
    @abstractmethod
    def total_amount(self) -> Decimal:
        """Return the total amount of the invoice."""
        pass
    
    @property
    @abstractmethod
    def paid_amount(self) -> Decimal:
        """Return the amount that has been paid."""
        pass
    
    @property
    @abstractmethod
    def due_amount(self) -> Decimal:
        """Return the amount still due."""
        pass
    
    @property
    @abstractmethod
    def expiration_date(self) -> Optional[datetime]:
        """Return the payment due date."""
        pass
    
    @property
    @abstractmethod
    def is_overdue(self) -> bool:
        """Return True if payment is overdue."""
        pass
    
    @abstractmethod
    def get_items(self) -> List[InvoiceItemInterface]:
        """
        Get all items in the invoice.
        
        Returns:
            List[InvoiceItemInterface]: List of invoice items
        """
        pass
    
    @abstractmethod
    def send(self):
        """
        Mark the invoice as sent.
        
        Changes status from DRAFT to SENT.
        """
        pass
    
    @abstractmethod
    def record_payment(self, amount: Decimal, payment_method: str = ''):
        """
        Record a payment against this invoice.
        
        Args:
            amount: Payment amount
            payment_method: Payment method used
        """
        pass
    
    @abstractmethod
    def mark_as_paid(self):
        """
        Mark invoice as fully paid.
        
        Changes status to PAID.
        """
        pass
    
    @abstractmethod
    def mark_as_overdue(self):
        """
        Mark invoice as overdue.
        
        Called when payment deadline has passed.
        """
        pass
    
    @abstractmethod
    def cancel(self):
        """
        Cancel the invoice.
        
        Changes status to CANCELLED.
        """
        pass
    
    @abstractmethod
    def generate_pdf(self) -> bytes:
        """
        Generate PDF representation of the invoice.
        
        Returns:
            bytes: PDF content
        """
        pass


__all__ = [
    'InvoiceStatus',
    'InvoiceItemInterface',
    'InvoiceInterface',
]