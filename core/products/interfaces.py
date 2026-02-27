# -*- coding: utf-8 -*-
"""
Product Interfaces - Abstract Base Classes for the Core Framework

This module defines the contracts that business applications must implement
to provide product-specific behavior. These interfaces ensure that the core
remains stable while allowing business apps to define their own product types.

Strategy Pattern:
- PricingInterface: Defines pricing strategy
- StockInterface: Defines stock management strategy
- ProductInterface: Defines general product behavior
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from decimal import Decimal
from django.http import HttpRequest


class ProductInterface(ABC):
    """
    Abstract base class for product behavior.
    
    All product types (retail, real estate, automotive, etc.) must implement
    this interface to be compatible with the core framework.
    """
    
    @abstractmethod
    def get_absolute_url(self) -> str:
        """Return the canonical URL for this product."""
        pass
    
    @abstractmethod
    def get_price(self, request: HttpRequest) -> Decimal:
        """
        Return the current price of this product.
        
        The price can vary based on:
        - User type (B2B vs B2C)
        - Quantity
        - Time-based promotions
        - Customer-specific discounts
        """
        pass
    
    @abstractmethod
    def get_availability(self, request: HttpRequest, **kwargs) -> 'Availability':
        """
        Check the availability of this product.
        
        Returns an Availability object with:
        - is_available: bool
        - message: str (optional reason if unavailable)
        - quantity: int (available quantity)
        """
        pass
    
    @property
    @abstractmethod
    def product_type(self) -> str:
        """Return the product type identifier (e.g., 'retail', 'immo', 'auto')."""
        pass
    
    def managed_availability(self) -> bool:
        """
        Return True if this product has quantity managed by inventory.
        
        Override this for products that don't need stock management
        (e.g., real estate, services).
        """
        return True


class Availability:
    """
    Represents product availability information.
    """
    
    def __init__(self, is_available: bool = True, message: str = '', quantity: int = 0):
        self.is_available = is_available
        self.message = message
        self.quantity = quantity
    
    def __bool__(self):
        return self.is_available


class PricingInterface(ABC):
    """
    Abstract base class for pricing strategies.
    
    Business applications can implement custom pricing logic by subclassing
    this interface and registering it with the pricing service.
    """
    
    @abstractmethod
    def calculate_price(
        self, 
        product: ProductInterface, 
        quantity: int = 1,
        customer: Optional[Any] = None,
        request: Optional[HttpRequest] = None
    ) -> Decimal:
        """
        Calculate the final price for a product.
        
        Args:
            product: The product to price
            quantity: Quantity being purchased
            customer: Optional customer for customer-specific pricing
            request: Optional HTTP request for context
            
        Returns:
            Decimal: The calculated price
        """
        pass
    
    @abstractmethod
    def calculate_tax(
        self, 
        product: ProductInterface, 
        price: Decimal,
        customer: Optional[Any] = None
    ) -> Decimal:
        """
        Calculate tax amount for a product.
        
        Args:
            product: The product
            price: The base price
            customer: Optional customer for tax jurisdiction
            
        Returns:
            Decimal: The tax amount
        """
        pass
    
    @abstractmethod
    def apply_discount(
        self, 
        price: Decimal, 
        discount_code: Optional[str] = None,
        customer: Optional[Any] = None
    ) -> Decimal:
        """
        Apply discount to a price.
        
        Args:
            price: The original price
            discount_code: Optional promotional code
            customer: Optional customer for customer-specific discounts
            
        Returns:
            Decimal: The discounted price
        """
        pass


class StockInterface(ABC):
    """
    Abstract base class for stock management strategies.
    
    Different business domains have different stock management needs:
    - Retail: Standard quantity management
    - Real Estate: No stock (unique properties)
    - Automotive: Vehicle inventory with VIN tracking
    - Services: No physical stock
    """
    
    @abstractmethod
    def check_availability(
        self, 
        product: ProductInterface, 
        quantity: int = 1
    ) -> Availability:
        """
        Check if the requested quantity is available.
        
        Args:
            product: The product to check
            quantity: Requested quantity
            
        Returns:
            Availability: Object indicating if available
        """
        pass
    
    @abstractmethod
    def reserve_stock(
        self, 
        product: ProductInterface, 
        quantity: int,
        order_id: str
    ) -> bool:
        """
        Reserve stock for an order.
        
        Args:
            product: The product to reserve
            quantity: Quantity to reserve
            order_id: The order identifier
            
        Returns:
            bool: True if reservation successful
        """
        pass
    
    @abstractmethod
    def decrement_stock(
        self, 
        product: ProductInterface, 
        quantity: int,
        reason: str = 'sale'
    ) -> bool:
        """
        Permanently decrement stock after delivery.
        
        Args:
            product: The product
            quantity: Quantity to decrement
            reason: Reason for decrement ('sale', 'damage', 'return', etc.)
            
        Returns:
            bool: True if decrement successful
        """
        pass
    
    @abstractmethod
    def increment_stock(
        self, 
        product: ProductInterface, 
        quantity: int,
        reason: str = 'restock'
    ) -> bool:
        """
        Increment stock (for returns, restocking, etc.).
        
        Args:
            product: The product
            quantity: Quantity to add
            reason: Reason for increment
            
        Returns:
            bool: True if increment successful
        """
        pass
    
    def get_stock_level(self, product: ProductInterface) -> int:
        """
        Get current stock level for a product.
        
        Override this for products that don't track stock.
        """
        return getattr(product, 'stock', 0)


class PaymentInterface(ABC):
    """
    Abstract base class for payment strategies.
    
    Business applications can implement different payment methods
    by implementing this interface.
    """
    
    @abstractmethod
    def process_payment(
        self, 
        amount: Decimal,
        payment_method: str,
        customer: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> 'PaymentResult':
        """
        Process a payment transaction.
        
        Args:
            amount: Payment amount
            payment_method: Payment method identifier
            customer: Optional customer
            metadata: Additional payment data
            
        Returns:
            PaymentResult: Result of the payment processing
        """
        pass
    
    @abstractmethod
    def refund_payment(
        self, 
        transaction_id: str,
        amount: Optional[Decimal] = None
    ) -> 'RefundResult':
        """
        Process a refund.
        
        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount
            
        Returns:
            RefundResult: Result of the refund
        """
        pass


class ShippingInterface(ABC):
    """
    Abstract base class for shipping strategies.
    """
    
    @abstractmethod
    def calculate_shipping(
        self, 
        weight: float,
        destination: str,
        items: Optional[list] = None
    ) -> Decimal:
        """
        Calculate shipping cost.
        
        Args:
            weight: Total weight of items
            destination: Destination address/zone
            items: Optional list of items for dimension calculations
            
        Returns:
            Decimal: Shipping cost
        """
        pass
    
    @abstractmethod
    def get_shipping_methods(self, destination: Optional[str] = None) -> list:
        """
        Get available shipping methods for a destination.
        
        Args:
            destination: Optional destination filter
            
        Returns:
            list: List of available shipping methods
        """
        pass
    
    @abstractmethod
    def track_shipment(self, tracking_number: str) -> Dict:
        """
        Get tracking information for a shipment.
        
        Args:
            tracking_number: Shipping tracking number
            
        Returns:
            Dict: Tracking information
        """
        pass


class PaymentResult:
    """Result of a payment processing operation."""
    
    def __init__(
        self, 
        success: bool, 
        transaction_id: str = '',
        message: str = '',
        error_code: Optional[str] = None
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.message = message
        self.error_code = error_code


class RefundResult:
    """Result of a refund operation."""
    
    def __init__(
        self, 
        success: bool, 
        refund_id: str = '',
        message: str = ''
    ):
        self.success = success
        self.refund_id = refund_id
        self.message = message