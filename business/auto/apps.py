# -*- coding: utf-8 -*-
"""
Business Application: Automotive

This app implements automotive specific features:
- Vehicle listings (cars, motorcycles, trucks)
- Spare parts inventory
- Garage services
- VIN-based vehicle tracking
"""

from django.apps import AppConfig
from core.services.stock import StockService, StandardStockStrategy


class AutoConfig(AppConfig):
    """Configuration for the Automotive business app."""
    
    name = 'business.auto'
    verbose_name = 'Automotive'
    
    def ready(self):
        """Register the standard stock strategy for automotive."""
        StockService.register_strategy('auto', StandardStockStrategy())