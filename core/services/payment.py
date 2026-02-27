# -*- coding: utf-8 -*-
"""
Payment Service - Strategy Pattern Implementation

This module implements the payment strategy for the core framework.
Business applications can implement different payment methods.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Optional, Dict
from django.utils import timezone


class PaymentStrategy(ABC):
    """
    Abstract base class for payment strategies.
    
    Business applications can implement custom payment methods
    by creating a subclass and registering it with the PaymentService.
    """
    
    @abstractmethod
    def process_payment(
        self,
        amount: Decimal,
        payment_method: str,
        customer: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process a payment transaction.
        
        Args:
            amount: Payment amount
            payment_method: Payment method identifier
            customer: Optional customer
            metadata: Additional payment data
            
        Returns:
            Dict: {
                'success': bool,
                'transaction_id': str,
                'message': str,
                'error_code': Optional[str]
            }
        """
        pass
    
    @abstractmethod
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict:
        """
        Process a refund.
        
        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount
            
        Returns:
            Dict: {
                'success': bool,
                'refund_id': str,
                'message': str
            }
        """
        pass
    
    @abstractmethod
    def get_payment_methods(self) -> list:
        """
        Get available payment methods for this strategy.
        
        Returns:
            list: List of payment method identifiers
        """
        pass


class DefaultPaymentStrategy(PaymentStrategy):
    """
    Default payment strategy (placeholder for actual payment gateway integration).
    """
    
    def process_payment(
        self,
        amount: Decimal,
        payment_method: str,
        customer: Optional[Any] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Process payment (simulated)."""
        # In production, this would integrate with a payment gateway
        return {
            'success': True,
            'transaction_id': f'TXN-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Payment processed successfully',
            'error_code': None
        }
    
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict:
        """Process refund (simulated)."""
        return {
            'success': True,
            'refund_id': f'REF-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            'message': 'Refund processed successfully'
        }
    
    def get_payment_methods(self) -> list:
        """Get available payment methods."""
        return ['cash', 'check', 'bank_transfer']


class PaymentService:
    """
    Service for managing payment strategies.
    
    This service uses the Strategy pattern to allow different
    payment implementations for different business domains.
    """
    
    _strategy: PaymentStrategy = None
    _custom_strategies: dict = {}
    
    @classmethod
    def set_strategy(cls, strategy: PaymentStrategy):
        """
        Set the default payment strategy.
        
        Args:
            strategy: The payment strategy to use
        """
        cls._strategy = strategy
    
    @classmethod
    def register_strategy(cls, business_type: str, strategy: PaymentStrategy):
        """
        Register a payment strategy for a specific business type.
        
        Args:
            business_type: Identifier for the business type
            strategy: The payment strategy to use
        """
        cls._custom_strategies[business_type] = strategy
    
    @classmethod
    def get_strategy(cls, business_type: Optional[str] = None) -> PaymentStrategy:
        """
        Get the payment strategy for a business type.
        
        Args:
            business_type: Optional business type identifier
            
        Returns:
            PaymentStrategy: The appropriate payment strategy
        """
        if business_type and business_type in cls._custom_strategies:
            return cls._custom_strategies[business_type]
        
        if cls._strategy is None:
            cls._strategy = DefaultPaymentStrategy()
        
        return cls._strategy
    
    @classmethod
    def process_payment(
        cls,
        amount: Decimal,
        payment_method: str,
        customer: Optional[Any] = None,
        metadata: Optional[Dict] = None,
        business_type: Optional[str] = None
    ) -> Dict:
        """
        Process a payment.
        
        Args:
            amount: Payment amount
            payment_method: Payment method identifier
            customer: Optional customer
            metadata: Additional payment data
            business_type: Optional business type
            
        Returns:
            Dict: Payment result
        """
        strategy = cls.get_strategy(business_type)
        return strategy.process_payment(amount, payment_method, customer, metadata)
    
    @classmethod
    def refund_payment(
        cls,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        business_type: Optional[str] = None
    ) -> Dict:
        """
        Process a refund.
        
        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount
            business_type: Optional business type
            
        Returns:
            Dict: Refund result
        """
        strategy = cls.get_strategy(business_type)
        return strategy.refund_payment(transaction_id, amount)
    
    @classmethod
    def get_payment_methods(
        cls,
        business_type: Optional[str] = None
    ) -> list:
        """
        Get available payment methods.
        
        Args:
            business_type: Optional business type
            
        Returns:
            list: Available payment methods
        """
        strategy = cls.get_strategy(business_type)
        return strategy.get_payment_methods()


# Default instance
PaymentService.set_strategy(DefaultPaymentStrategy())


__all__ = [
    'PaymentStrategy',
    'DefaultPaymentStrategy',
    'PaymentService',
]