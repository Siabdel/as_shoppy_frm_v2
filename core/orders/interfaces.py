# -*- coding: utf-8 -*-
"""
Order Interfaces - Abstract Base Classes for Order Management

This module defines the contracts for order operations.
The order is the third step in the business workflow:
Catalog -> Cart -> Quote -> Order -> Invoice
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from decimal import Decimal
from django.http import HttpRequest
from datetime import datetime


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
        (CREATED, 'Created'),
        (AWAITING_PAYMENT, 'Awaiting Payment'),
        (PAID, 'Paid'),
        (SHIPPED, 'Shipped'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    ]


class OrderItemInterface(ABC):
    """
    Abstract base class for order item behavior.
    """
    
    @property
    @abstractmethod
    def product(self) -> Any:
        """Return the product associated with this order item."""
        pass
    
    @property
    @abstractmethod
    def quantity(self) -> int:
        """Return the quantity of the product."""
        pass
    
    @property
    @abstractmethod
    def unit_price(self) -> Decimal:
        """Return the unit price at time of order creation."""
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
    def is_reserved(self) -> bool:
        """Return True if stock has been reserved for this item."""
        pass
    
    @property
    @abstractmethod
    def is_shipped(self) -> bool:
        """Return True if this item has been shipped."""
        pass


class OrderInterface(ABC):
    """
    Abstract base class for order behavior.
    
    An order is created from an accepted quote and represents
    a confirmed transaction. It goes through several status
    transitions until completion.
    
    Workflow: Quote -> Order -> Invoice
    
    Stock Management:
    - Reservation: At order time (reserve stock)
    - Decrement: On delivery (permanent reduction)
    """
    
    @property
    @abstractmethod
    def order_number(self) -> str:
        """Return the unique order number."""
        pass
    
    @property
    @abstractmethod
    def status(self) -> str:
        """Return the current status of the order."""
        pass
    
    @property
    @abstractmethod
    def customer(self) -> Any:
        """Return the customer associated with this order."""
        pass
    
    @property
    @abstractmethod
    def total_amount(self) -> Decimal:
        """Return the total amount of the order."""
        pass
    
    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Return the creation date of the order."""
        pass
    
    @abstractmethod
    def get_items(self) -> List[OrderItemInterface]:
        """
        Get all items in the order.
        
        Returns:
            List[OrderItemInterface]: List of order items
        """
        pass
    
    @abstractmethod
    def reserve_stock(self) -> bool:
        """
        Reserve stock for all items in the order.
        
        Called when order is created to reserve inventory.
        
        Returns:
            bool: True if all reservations successful
        """
        pass
    
    @abstractmethod
    def release_stock(self):
        """
        Release reserved stock.
        
        Called when order is cancelled.
        """
        pass
    
    @abstractmethod
    def decrement_stock(self) -> bool:
        """
        Permanently decrement stock for all items.
        
        Called when order is delivered/shipped.
        
        Returns:
            bool: True if all decrements successful
        """
        pass
    
    @abstractmethod
    def mark_as_paid(self):
        """
        Mark order as paid.
        
        Changes status from AWAITING_PAYMENT to PAID.
        Triggers stock reservation.
        """
        pass
    
    @abstractmethod
    def mark_as_shipped(self):
        """
        Mark order as shipped.
        
        Changes status from PAID to SHIPPED.
        Triggers stock decrement.
        """
        pass
    
    @abstractmethod
    def mark_as_completed(self):
        """
        Mark order as completed.
        
        Changes status from SHIPPED to COMPLETED.
        """
        pass
    
    @abstractmethod
    def mark_as_cancelled(self):
        """
        Mark order as cancelled.
        
        Changes status to CANCELLED.
        Releases any reserved stock.
        """
        pass
    
    @abstractmethod
    def to_invoice(self, request: HttpRequest) -> Any:
        """
        Convert the order to an invoice.
        
        This is the Order -> Invoice step in the workflow.
        
        Args:
            request: HTTP request for context
            
        Returns:
            Invoice: The created invoice
        """
        pass
    
    @abstractmethod
    def is_paid(self) -> bool:
        """Return True if order has been paid."""
        pass
    
    @abstractmethod
    def is_cancelled(self) -> bool:
        """Return True if order has been cancelled."""
        pass


__all__ = [
    'OrderStatus',
    'OrderItemInterface',
    'OrderInterface',
]