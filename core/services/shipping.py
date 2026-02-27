# -*- coding: utf-8 -*-
"""
Shipping Service - Strategy Pattern Implementation

This module implements the shipping strategy for the core framework.
Business applications can implement different shipping methods.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional, Dict, List
from django.utils import timezone


class ShippingStrategy(ABC):
    """
    Abstract base class for shipping strategies.
    
    Business applications can implement custom shipping methods
    by creating a subclass and registering it with the ShippingService.
    """
    
    @abstractmethod
    def calculate_shipping(
        self,
        weight: float,
        destination: str,
        items: Optional[List] = None
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
    def get_shipping_methods(
        self,
        destination: Optional[str] = None
    ) -> List[Dict]:
        """
        Get available shipping methods for a destination.
        
        Args:
            destination: Optional destination filter
            
        Returns:
            List[Dict]: List of available shipping methods
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
    
    @abstractmethod
    def create_shipment(
        self,
        order: Any,
        shipping_method: str,
        destination: Dict
    ) -> Dict:
        """
        Create a shipment for an order.
        
        Args:
            order: The order to ship
            shipping_method: Selected shipping method
            destination: Shipping destination
            
        Returns:
            Dict: Shipment information including tracking number
        """
        pass


class DefaultShippingStrategy(ShippingStrategy):
    """
    Default shipping strategy with basic rate calculations.
    """
    
    def calculate_shipping(
        self,
        weight: float,
        destination: str,
        items: Optional[List] = None
    ) -> Decimal:
        """Calculate shipping based on weight and destination."""
        # Base rate
        base_rate = Decimal('10.00')
        
        # Weight factor
        weight_rate = Decimal(str(weight)) * Decimal('0.50')
        
        # Destination factor (simplified)
        dest_factor = Decimal('1.0')
        if destination and destination.lower().startswith('fr'):
            dest_factor = Decimal('1.0')  # France
        elif destination and destination.lower().startswith('eu'):
            dest_factor = Decimal('1.5')  # Europe
        else:
            dest_factor = Decimal('2.0')  # International
        
        return (base_rate + weight_rate) * dest_factor
    
    def get_shipping_methods(
        self,
        destination: Optional[str] = None
    ) -> List[Dict]:
        """Get available shipping methods."""
        methods = [
            {
                'id': 'standard',
                'name': 'Standard Shipping',
                'description': '5-7 business days',
                'base_cost': Decimal('10.00')
            },
            {
                'id': 'express',
                'name': 'Express Shipping',
                'description': '2-3 business days',
                'base_cost': Decimal('25.00')
            },
            {
                'id': 'overnight',
                'name': 'Overnight Shipping',
                'description': 'Next business day',
                'base_cost': Decimal('50.00')
            }
        ]
        
        if destination and destination.lower().startswith('fr'):
            # Add free shipping for France on orders over 100
            methods.append({
                'id': 'free',
                'name': 'Free Shipping',
                'description': 'Free for orders over 100€',
                'base_cost': Decimal('0.00'),
                'min_order': Decimal('100.00')
            })
        
        return methods
    
    def track_shipment(self, tracking_number: str) -> Dict:
        """Get tracking information (placeholder)."""
        return {
            'tracking_number': tracking_number,
            'status': 'in_transit',
            'estimated_delivery': None,
            'events': [
                {
                    'timestamp': timezone.now().isoformat(),
                    'location': 'Distribution Center',
                    'description': 'Package in transit'
                }
            ]
        }
    
    def create_shipment(
        self,
        order: Any,
        shipping_method: str,
        destination: Dict
    ) -> Dict:
        """Create a shipment (placeholder)."""
        tracking_number = f'TRK-{order.numero}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        
        return {
            'success': True,
            'tracking_number': tracking_number,
            'shipping_method': shipping_method,
            'label_url': None
        }


class ShippingService:
    """
    Service for managing shipping strategies.
    
    This service uses the Strategy pattern to allow different
    shipping implementations for different business domains.
    """
    
    _strategy: ShippingStrategy = None
    _custom_strategies: dict = {}
    
    @classmethod
    def set_strategy(cls, strategy: ShippingStrategy):
        """
        Set the default shipping strategy.
        
        Args:
            strategy: The shipping strategy to use
        """
        cls._strategy = strategy
    
    @classmethod
    def register_strategy(cls, business_type: str, strategy: ShippingStrategy):
        """
        Register a shipping strategy for a specific business type.
        
        Args:
            business_type: Identifier for the business type
            strategy: The shipping strategy to use
        """
        cls._custom_strategies[business_type] = strategy
    
    @classmethod
    def get_strategy(cls, business_type: Optional[str] = None) -> ShippingStrategy:
        """
        Get the shipping strategy for a business type.
        
        Args:
            business_type: Optional business type identifier
            
        Returns:
            ShippingStrategy: The appropriate shipping strategy
        """
        if business_type and business_type in cls._custom_strategies:
            return cls._custom_strategies[business_type]
        
        if cls._strategy is None:
            cls._strategy = DefaultShippingStrategy()
        
        return cls._strategy
    
    @classmethod
    def calculate_shipping(
        cls,
        weight: float,
        destination: str,
        items: Optional[List] = None,
        business_type: Optional[str] = None
    ) -> Decimal:
        """
        Calculate shipping cost.
        
        Args:
            weight: Total weight
            destination: Destination
            items: Optional items
            business_type: Optional business type
            
        Returns:
            Decimal: Shipping cost
        """
        strategy = cls.get_strategy(business_type)
        return strategy.calculate_shipping(weight, destination, items)
    
    @classmethod
    def get_shipping_methods(
        cls,
        destination: Optional[str] = None,
        business_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get available shipping methods.
        
        Args:
            destination: Optional destination
            business_type: Optional business type
            
        Returns:
            List[Dict]: Available shipping methods
        """
        strategy = cls.get_strategy(business_type)
        return strategy.get_shipping_methods(destination)
    
    @classmethod
    def track_shipment(
        cls,
        tracking_number: str,
        business_type: Optional[str] = None
    ) -> Dict:
        """
        Track a shipment.
        
        Args:
            tracking_number: Tracking number
            business_type: Optional business type
            
        Returns:
            Dict: Tracking information
        """
        strategy = cls.get_strategy(business_type)
        return strategy.track_shipment(tracking_number)
    
    @classmethod
    def create_shipment(
        cls,
        order: Any,
        shipping_method: str,
        destination: Dict,
        business_type: Optional[str] = None
    ) -> Dict:
        """
        Create a shipment.
        
        Args:
            order: The order
            shipping_method: Selected method
            destination: Destination
            business_type: Optional business type
            
        Returns:
            Dict: Shipment information
        """
        strategy = cls.get_strategy(business_type)
        return strategy.create_shipment(order, shipping_method, destination)


# Default instance
ShippingService.set_strategy(DefaultShippingStrategy())


__all__ = [
    'ShippingStrategy',
    'DefaultShippingStrategy',
    'ShippingService',
]