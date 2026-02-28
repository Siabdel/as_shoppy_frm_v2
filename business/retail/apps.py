# -*- coding: utf-8 -*-
"""
Business Application: Retail (E-commerce)

This app implements retail e-commerce specific features:
- Standard product management with stock
- Product variants (size, color)
- Wishlist
- Standard pricing and shipping
"""

from django.apps import AppConfig
from core.services.stock import StockService, StandardStockStrategy


class RetailConfig(AppConfig):
    """Configuration for the Retail business app."""
    
    name = 'business.retail'
    verbose_name = 'Retail E-commerce'
    
    def ready(self):
        """Register the standard stock strategy for retail."""
        StockService.register_strategy('retail', StandardStockStrategy())