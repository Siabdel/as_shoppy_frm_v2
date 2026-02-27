# Core Quotes Module
# This module contains the base quote models and interfaces

from core.quotes.models import BaseQuote, BaseQuoteItem, QuoteStatus
from core.quotes.interfaces import QuoteInterface, QuoteItemInterface

__all__ = [
    'BaseQuote',
    'BaseQuoteItem',
    'QuoteStatus',
    'QuoteInterface',
    'QuoteItemInterface',
]