# -*- coding: utf-8 -*-
"""
Stock Service - Strategy Pattern Implementation

This module implements the stock management strategy for the core framework.
Different business domains can have different stock management needs:
- Retail: Standard quantity management
- Real Estate: No stock (unique properties)
- Automotive: Vehicle inventory with VIN tracking
- Services: No physical stock
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional
from django.utils import timezone


class StockStrategy(ABC):
    """
    Abstract base class for stock strategies.
    
    Business applications can implement custom stock management
    by creating a subclass and registering it with the StockService.
    """
    
    @abstractmethod
    def check_availability(
        self,
        product: Any,
        quantity: int = 1
    ) -> tuple:
        """
        Check if the requested quantity is available.
        
        Args:
            product: The product to check
            quantity: Requested quantity
            
        Returns:
            tuple: (is_available: bool, message: str, quantity: int)
        """
        pass
    
    @abstractmethod
    def reserve_stock(
        self,
        product: Any,
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
        product: Any,
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
        product: Any,
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
    
    def get_stock_level(self, product: Any) -> int:
        """
        Get current stock level for a product.
        
        Override this for products that don't track stock.
        """
        return getattr(product, 'stock', 0)


class StandardStockStrategy(StockStrategy):
    """
    Standard stock strategy for retail products.
    
    Manages stock quantities with reservation and decrement.
    """
    
    def check_availability(self, product: Any, quantity: int = 1) -> tuple:
        """Check if requested quantity is available."""
        stock = getattr(product, 'stock', 0)
        is_available = stock >= quantity
        
        if is_available:
            return (True, '', stock)
        return (False, f'Only {stock} available', stock)
    
    def reserve_stock(self, product: Any, quantity: int, order_id: str) -> bool:
        """Reserve stock for an order."""
        is_available, _, _ = self.check_availability(product, quantity)
        
        if not is_available:
            return False
        
        # Create reservation record
        from core.stock.models import StockReservation
        StockReservation.objects.create(
            product=product,
            quantity=quantity,
            order_id=order_id,
            status='reserved'
        )
        
        return True
    
    def decrement_stock(self, product: Any, quantity: int, reason: str = 'sale') -> bool:
        """Permanently decrement stock."""
        current_stock = getattr(product, 'stock', 0)
        
        if current_stock < quantity:
            return False
        
        product.stock = current_stock - quantity
        product.save()
        
        # Record stock movement
        from core.stock.models import StockMovement
        StockMovement.objects.create(
            product=product,
            quantity=-quantity,
            reason=reason,
            reference=f'decrement_{reason}'
        )
        
        return True
    
    def increment_stock(self, product: Any, quantity: int, reason: str = 'restock') -> bool:
        """Increment stock."""
        current_stock = getattr(product, 'stock', 0)
        product.stock = current_stock + quantity
        product.save()
        
        # Record stock movement
        from core.stock.models import StockMovement
        StockMovement.objects.create(
            product=product,
            quantity=quantity,
            reason=reason,
            reference=f'increment_{reason}'
        )
        
        return True


class NoStockStrategy(StockStrategy):
    """
    No-stock strategy for products that don't track inventory.
    
    Used for:
    - Real estate (unique properties)
    - Services
    - Digital products
    """
    
    def check_availability(self, product: Any, quantity: int = 1) -> tuple:
        """Always available."""
        return (True, 'Available', 999999)
    
    def reserve_stock(self, product: Any, quantity: int, order_id: str) -> bool:
        """No-op for no-stock products."""
        return True
    
    def decrement_stock(self, product: Any, quantity: int, reason: str = 'sale') -> bool:
        """No-op for no-stock products."""
        return True
    
    def increment_stock(self, product: Any, quantity: int, reason: str = 'restock') -> bool:
        """No-op for no-stock products."""
        return True
    
    def get_stock_level(self, product: Any) -> int:
        """Return unlimited stock."""
        return 999999


class StockService:
    """
    Service for managing stock strategies.
    
    This service uses the Strategy pattern to allow different
    stock management implementations for different business domains.
    """
    
    _strategy: StockStrategy = None
    _custom_strategies: dict = {}
    
    @classmethod
    def set_strategy(cls, strategy: StockStrategy):
        """
        Set the default stock strategy.
        
        Args:
            strategy: The stock strategy to use
        """
        cls._strategy = strategy
    
    @classmethod
    def register_strategy(cls, business_type: str, strategy: StockStrategy):
        """
        Register a stock strategy for a specific business type.
        
        Args:
            business_type: Identifier for the business type (e.g., 'immo', 'auto')
            strategy: The stock strategy to use for this business type
        """
        cls._custom_strategies[business_type] = strategy
    
    @classmethod
    def get_strategy(cls, business_type: Optional[str] = None) -> StockStrategy:
        """
        Get the stock strategy for a business type.
        
        Args:
            business_type: Optional business type identifier
            
        Returns:
            StockStrategy: The appropriate stock strategy
        """
        if business_type and business_type in cls._custom_strategies:
            return cls._custom_strategies[business_type]
        
        if cls._strategy is None:
            cls._strategy = StandardStockStrategy()
        
        return cls._strategy
    
    @classmethod
    def check_availability(
        cls,
        product: Any,
        quantity: int = 1,
        business_type: Optional[str] = None
    ) -> tuple:
        """
        Check if product is available in requested quantity.
        
        Args:
            product: The product to check
            quantity: Requested quantity
            business_type: Optional business type
            
        Returns:
            tuple: (is_available, message, available_quantity)
        """
        strategy = cls.get_strategy(business_type)
        return strategy.check_availability(product, quantity)
    
    @classmethod
    def reserve_stock(
        cls,
        product: Any,
        quantity: int,
        order_id: str,
        business_type: Optional[str] = None
    ) -> bool:
        """
        Reserve stock for an order.
        
        Args:
            product: The product to reserve
            quantity: Quantity to reserve
            order_id: The order identifier
            business_type: Optional business type
            
        Returns:
            bool: True if reservation successful
        """
        strategy = cls.get_strategy(business_type)
        return strategy.reserve_stock(product, quantity, order_id)
    
    @classmethod
    def decrement_stock(
        cls,
        product: Any,
        quantity: int,
        reason: str = 'sale',
        business_type: Optional[str] = None
    ) -> bool:
        """
        Permanently decrement stock.
        
        Args:
            product: The product
            quantity: Quantity to decrement
            reason: Reason for decrement
            business_type: Optional business type
            
        Returns:
            bool: True if decrement successful
        """
        strategy = cls.get_strategy(business_type)
        return strategy.decrement_stock(product, quantity, reason)
    
    @classmethod
    def increment_stock(
        cls,
        product: Any,
        quantity: int,
        reason: str = 'restock',
        business_type: Optional[str] = None
    ) -> bool:
        """
        Increment stock.
        
        Args:
            product: The product
            quantity: Quantity to add
            reason: Reason for increment
            business_type: Optional business type
            
        Returns:
            bool: True if increment successful
        """
        strategy = cls.get_strategy(business_type)
        return strategy.increment_stock(product, quantity, reason)
    
    @classmethod
    def get_stock_level(
        cls,
        product: Any,
        business_type: Optional[str] = None
    ) -> int:
        """
        Get current stock level.
        
        Args:
            product: The product
            business_type: Optional business type
            
        Returns:
            int: Current stock level
        """
        strategy = cls.get_strategy(business_type)
        return strategy.get_stock_level(product)


# Default instance
StockService.set_strategy(StandardStockStrategy())


__all__ = [
    'StockStrategy',
    'StandardStockStrategy',
    'NoStockStrategy',
    'StockService',
]