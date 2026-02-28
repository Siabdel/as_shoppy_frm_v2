# Core Orders Module
# This module contains the base order models and interfaces
#
# Note: Models are not imported at module level to avoid
# AppRegistryNotReady errors. Import them directly where needed:
#   from core.orders.models import BaseOrder, BaseOrderItem, OrderStatus
#   from core.orders.interfaces import OrderInterface, OrderItemInterface