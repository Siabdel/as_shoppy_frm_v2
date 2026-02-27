# -*- coding: utf-8 -*-
"""
Quote Interfaces - Abstract Base Classes for Quote Management

This module defines the contracts for quote (devis) operations.
The quote is the second step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from decimal import Decimal
from django.http import HttpRequest
from datetime import datetime


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
        (DRAFT, 'Draft'),
        (SENT, 'Sent'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (EXPIRED, 'Expired'),
        (CONVERTED, 'Converted to Order'),
    ]


class QuoteItemInterface(ABC):
    """
    Abstract base class for quote item behavior.
    """
    
    @property
    @abstractmethod
    def product(self) -> Any:
        """Return the product associated with this quote item."""
        pass
    
    @property
    @abstractmethod
    def quantity(self) -> int:
        """Return the quantity of the product."""
        pass
    
    @property
    @abstractmethod
    def unit_price(self) -> Decimal:
        """Return the unit price at time of quote creation."""
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


class QuoteInterface(ABC):
    """
    Abstract base class for quote behavior.
    
    The quote is created from a cart and represents a formal proposal
    to the customer. It has an expiration date and can be accepted,
    rejected, or converted to an order.
    
    Workflow: Cart -> Quote -> Order -> Invoice
    """
    
    @property
    @abstractmethod
    def quote_number(self) -> str:
        """Return the unique quote number."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Return the current status of the quote."""
        pass
    
    @property
    @abstractmethod
    def customer(self) -> Any:
        """Return the customer associated with this quote."""
        pass
    
    @property
    @abstractmethod
    def total_amount(self) -> Decimal:
        """Return the total amount of the quote."""
        pass
    
    @property
    @abstractmethod
    def expiration_date(self) -> Optional[datetime]:
        """Return the expiration date of the quote."""
        pass
    
    @abstractmethod
    def get_items(self) -> List[QuoteItemInterface]:
        """
        Get all items in the quote.
        
        Returns:
            List[QuoteItemInterface]: List of quote items
        """
        pass
    
    @abstractmethod
    def send(self):
        """
        Mark the quote as sent.
        
        Changes status from DRAFT to SENT.
        """
        pass
    
    @abstractmethod
    def accept(self):
        """
        Mark the quote as accepted.
        
        Changes status from SENT to ACCEPTED.
        This makes the quote eligible for conversion to an order.
        """
        pass
    
    @abstractmethod
    def reject(self):
        """
        Mark the quote as rejected.
        
        Changes status from SENT to REJECTED.
        """
        pass
    
    @abstractmethod
    def expire(self):
        """
        Mark the quote as expired.
        
        Changes status to EXPIRED if past expiration date.
        """
        pass
    
    @abstractmethod
    def to_order(self, request: HttpRequest) -> Any:
        """
        Convert the quote to an order.
        
        This is the Quote -> Order step in the workflow.
        Only accepted quotes can be converted to orders.
        
        Args:
            request: HTTP request for context
            
        Returns:
            Order: The created order
            
        Raises:
            ValueError: If quote is not accepted
        """
        pass
    
    @abstractmethod
    def is_valid_for_conversion(self) -> bool:
        """
        Check if the quote can be converted to an order.
        
        Returns:
            bool: True if quote is accepted and not expired
        """
        pass


__all__ = [
    'QuoteStatus',
    'QuoteItemInterface',
    'QuoteInterface',
]