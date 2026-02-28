# -*- coding: utf-8 -*-
"""
Business Application: Real Estate (Immo)

This app implements real estate specific features:
- Property listings (apartments, houses, lands)
- Property management (mandates, visits)
- No stock management (unique properties)
- Reservation handling instead of quantities
"""

from django.apps import AppConfig
from core.services.stock import StockService, NoStockStrategy


class ImmoConfig(AppConfig):
    """Configuration for the Real Estate business app."""
    
    name = 'business.immo'
    verbose_name = 'Real Estate'
    
    def ready(self):
        """Register the no-stock strategy for real estate."""
        StockService.register_strategy('immo', NoStockStrategy())