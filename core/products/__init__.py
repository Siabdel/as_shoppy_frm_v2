# Core Products Module
# This module contains the base product models and interfaces for the framework

from core.products.models import BaseProduct, BaseProductManager
from core.products.interfaces import (
    ProductInterface,
    PricingInterface,
    StockInterface,
)

__all__ = [
    'BaseProduct',
    'BaseProductManager',
    'ProductInterface',
    'PricingInterface',
    'StockInterface',
]