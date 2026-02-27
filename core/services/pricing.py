# -*- coding: utf-8 -*-
"""
Pricing Service - Strategy Pattern Implementation

This module implements the pricing strategy for the core framework.
Business applications can register custom pricing strategies.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional
from django.http import HttpRequest


class PricingStrategy(ABC):
    """
    Abstract base class for pricing strategies.
    
    Business applications can implement custom pricing by creating
    a subclass and registering it with the PricingService.
    """
    
    @abstractmethod
    def calculate_price(
        self,
        product: Any,
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
        product: Any,
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


class DefaultPricingStrategy(PricingStrategy):
    """
    Default pricing strategy that uses the product's base price.
    """
    
    def calculate_price(
        self,
        product: Any,
        quantity: int = 1,
        customer: Optional[Any] = None,
        request: Optional[HttpRequest] = None
    ) -> Decimal:
        """Use the product's base price."""
        return getattr(product, 'price', Decimal('0'))
    
    def calculate_tax(
        self,
        product: Any,
        price: Decimal,
        customer: Optional[Any] = None
    ) -> Decimal:
        """Calculate tax using product's tax rate."""
        tax_rate = getattr(product, 'sales_tax', 0)
        return price * Decimal(str(tax_rate)) / 100


class PricingService:
    """
    Service for managing pricing strategies.
    
    This service uses the Strategy pattern to allow different
    pricing implementations for different business domains.
    """
    
    _strategy: PricingStrategy = None
    _custom_strategies: dict = {}
    
    @classmethod
    def set_strategy(cls, strategy: PricingStrategy):
        """
        Set the default pricing strategy.
        
        Args:
            strategy: The pricing strategy to use
        """
        cls._strategy = strategy
    
    @classmethod
    def register_strategy(cls, business_type: str, strategy: PricingStrategy):
        """
        Register a pricing strategy for a specific business type.
        
        Args:
            business_type: Identifier for the business type (e.g., 'immo', 'auto')
            strategy: The pricing strategy to use for this business type
        """
        cls._custom_strategies[business_type] = strategy
    
    @classmethod
    def get_strategy(cls, business_type: Optional[str] = None) -> PricingStrategy:
        """
        Get the pricing strategy for a business type.
        
        Args:
            business_type: Optional business type identifier
            
        Returns:
            PricingStrategy: The appropriate pricing strategy
        """
        if business_type and business_type in cls._custom_strategies:
            return cls._custom_strategies[business_type]
        
        if cls._strategy is None:
            cls._strategy = DefaultPricingStrategy()
        
        return cls._strategy
    
    @classmethod
    def calculate_price(
        cls,
        product: Any,
        quantity: int = 1,
        customer: Optional[Any] = None,
        request: Optional[HttpRequest] = None,
        business_type: Optional[str] = None
    ) -> Decimal:
        """
        Calculate price using the appropriate strategy.
        
        Args:
            product: The product to price
            quantity: Quantity being purchased
            customer: Optional customer for customer-specific pricing
            request: Optional HTTP request for context
            business_type: Optional business type identifier
            
        Returns:
            Decimal: The calculated price
        """
        strategy = cls.get_strategy(business_type)
        return strategy.calculate_price(product, quantity, customer, request)
    
    @classmethod
    def calculate_tax(
        cls,
        product: Any,
        price: Decimal,
        customer: Optional[Any] = None,
        business_type: Optional[str] = None
    ) -> Decimal:
        """
        Calculate tax using the appropriate strategy.
        
        Args:
            product: The product
            price: The base price
            customer: Optional customer for tax jurisdiction
            business_type: Optional business type identifier
            
        Returns:
            Decimal: The tax amount
        """
        strategy = cls.get_strategy(business_type)
        return strategy.calculate_tax(product, price, customer)
    
    @classmethod
    def calculate_total(
        cls,
        items: list,
        customer: Optional[Any] = None,
        request: Optional[HttpRequest] = None,
        business_type: Optional[str] = None
    ) -> tuple:
        """
        Calculate total price and tax for a list of items.
        
        Args:
            items: List of (product, quantity) tuples
            customer: Optional customer
            request: Optional HTTP request
            business_type: Optional business type
            
        Returns:
            tuple: (subtotal, tax_amount, total)
        """
        subtotal = Decimal('0')
        tax_amount = Decimal('0')
        
        for product, quantity in items:
            price = cls.calculate_price(
                product, quantity, customer, request, business_type
            )
            tax = cls.calculate_tax(product, price, customer, business_type)
            
            subtotal += price * quantity
            tax_amount += tax * quantity
        
        total = subtotal + tax_amount
        return subtotal, tax_amount, total


# Default instance
PricingService.set_strategy(DefaultPricingStrategy())


__all__ = [
    'PricingStrategy',
    'DefaultPricingStrategy',
    'PricingService',
]