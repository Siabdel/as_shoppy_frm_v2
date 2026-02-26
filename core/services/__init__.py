"""
Core Services Module

Provides a service layer for business logic encapsulation.
Services handle complex operations, workflow management,
and cross-model interactions.
"""

from .base import BaseService, ServiceError, ValidationError
from .order_service import OrderService
from .quote_service import QuoteService
from .invoice_service import InvoiceService
from .project_service import ProjectService

__all__ = [
    'BaseService',
    'ServiceError',
    'ValidationError',
    'OrderService',
    'QuoteService',
    'InvoiceService',
    'ProjectService',
]