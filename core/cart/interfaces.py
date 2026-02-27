# -*- coding: utf-8 -*-
"""
Cart Interfaces - Abstract Base Classes for Cart Management

This module defines the contracts for cart operations.
The Strategy pattern is used to allow different cart implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List
from decimal import Decimal
from django.http import HttpRequest


class CartItemInterface(ABC):
    """
    Abstract base class for cart item behavior.
    """
    
    @property
    @abstractmethod
    def product(self) -> Any:
        """Return the product associated with this cart item."""
        pass
    
    @property
    @abstractmethod
    def quantity(self) -> int:
        """Return the quantity of the product."""
        pass
    
    @quantity.setter
    @abstractmethod
    def quantity(self, value: int):
        """Set the quantity of the product."""
        pass
    
    @property
    @abstractmethod
    def unit_price(self) -> Decimal:
        """Return the unit price at time of adding to cart."""
        pass
    
    @property
    @abstractmethod
    def total_price(self) -> Decimal:
        """Return the total price (quantity * unit_price)."""
        pass
    
    @abstractmethod
    def update_quantity(self, quantity: int):
        """Update the quantity of this cart item."""
        pass


class CartInterface(ABC):
    """
    Abstract base class for cart behavior.
    
    The cart is the first step in the business workflow:
    Catalog -> Cart -> Quote -> Order -> Invoice
    
    Business applications can implement custom cart logic by subclassing
    this interface.
    """
    
    @abstractmethod
    def add_product(
        self, 
        product: Any, 
        quantity: int = 1, 
        update_quantity: bool = False
    ) -> CartItemInterface:
        """
        Add a product to the cart.
        
        Args:
            product: The product to add (must implement ProductInterface)
            quantity: Quantity to add
            update_quantity: If True, replace quantity; if False, add to existing
            
        Returns:
            CartItemInterface: The created/updated cart item
        """
        pass
    
    @abstractmethod
    def remove_product(self, product: Any) -> bool:
        """
        Remove a product from the cart.
        
        Args:
            product: The product to remove
            
        Returns:
            bool: True if product was removed, False if not found
        """
        pass
    
    @abstractmethod
    def update_product_quantity(
        self, 
        product: Any, 
        quantity: int
    ) -> CartItemInterface:
        """
        Update the quantity of a product in the cart.
        
        Args:
            product: The product to update
            quantity: New quantity (0 to remove)
            
        Returns:
            CartItemInterface: The updated cart item
        """
        pass
    
    @abstractmethod
    def get_items(self) -> List[CartItemInterface]:
        """
        Get all items in the cart.
        
        Returns:
            List[CartItemInterface]: List of cart items
        """
        pass
    
    @property
    @abstractmethod
    def total_price(self) -> Decimal:
        """Return the total price of all items in the cart."""
        pass
    
    @property
    @abstractmethod
    def item_count(self) -> int:
        """Return the total number of items in the cart."""
        pass
    
    @property
    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if the cart is empty."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all items from the cart."""
        pass
    
    @abstractmethod
    def to_quote(self, request: HttpRequest) -> Any:
        """
        Convert the cart to a quote (Devis).
        
        This is the Cart -> Quote step in the workflow.
        
        Args:
            request: HTTP request for context
            
        Returns:
            Quote: The created quote
        """
        pass
    
    @abstractmethod
    def merge(self, other_cart: 'CartInterface'):
        """
        Merge another cart into this one.
        
        Used when anonymous user logs in and their session cart
        needs to be merged with their saved cart.
        
        Args:
            other_cart: The cart to merge from
        """
        pass
    
    @abstractmethod
    def get_expiration_date(self) -> Optional[Any]:
        """
        Get the expiration date of the cart.
        
        Carts can expire after a period of inactivity.
        
        Returns:
            datetime: Expiration date, or None if cart doesn't expire
        """
        pass


class CartSessionInterface(ABC):
    """
    Abstract base class for cart session handling.
    
    Handles cart persistence across requests (session, database, etc.)
    """
    
    @abstractmethod
    def get_cart(self, request: HttpRequest) -> CartInterface:
        """
        Get the current cart for a request.
        
        Args:
            request: HTTP request
            
        Returns:
            CartInterface: The current cart
        """
        pass
    
    @abstractmethod
    def save_cart(self, request: HttpRequest, cart: CartInterface):
        """
        Save the cart to the session/database.
        
        Args:
            request: HTTP request
            cart: The cart to save
        """
        pass
    
    @abstractmethod
    def destroy_cart(self, request: HttpRequest):
        """
        Destroy the cart (logout, checkout complete, etc.)
        
        Args:
            request: HTTP request
        """
        pass