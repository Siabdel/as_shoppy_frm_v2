"""
Order Service Module

Handles business logic for order management including
workflow operations and cross-model interactions.
"""

from typing import Dict, Any, Optional

from django.db import transaction

from .base import BaseService, ServiceResult, ValidationError
from core.enums import OrderStatus
from core.state_machine import OrderWorkflow, WorkflowMixin


class OrderService(BaseService):
    """
    Service for managing orders and their lifecycle.
    """
    
    from core.orders.models import Order
    model_class = Order
    workflow_class = OrderWorkflow
    
    def __init__(self, user=None, context: Optional[Dict[str, Any]] = None):
        super().__init__(user, context)
        self.cart_service = CartService(user, context)
    
    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Validate order data."""
        errors = {}
        
        # Required fields
        required = [
            'first_name', 'last_name', 'email',
            'address', 'postal_code', 'city'
        ]
        for field in required:
            if not data.get(field):
                errors[field] = f"{field} is required"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def create_from_cart(
        self,
        cart_id: int,
        order_data: Dict[str, Any]
    ) -> ServiceResult:
        """
        Create an order from a shopping cart.
        
        Args:
            cart_id: ID of the cart to convert
            order_data: Order details (customer info, etc.)
            
        Returns:
            ServiceResult with created order
        """
        from shop.models import ShopCart
        
        try:
            cart = ShopCart.objects.get(id=cart_id)
            
            # Validate cart has items
            if not cart.items.exists():
                return ServiceResult.fail("Cart is empty")
            
            # Create order
            validated_data = self.validate(order_data)
            
            with transaction.atomic():
                # Create order
                order = self.perform_create(validated_data)
                
                # Create order items from cart items
                from core.orders.models import OrderItem
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        price=cart_item.product.price,
                        quantity=cart_item.quantity
                    )
                
                # Clear cart
                cart.items.all().delete()
                cart.save()
                
                self.after_create(order, validated_data)
            
            return ServiceResult.ok(order, "Order created successfully")
            
        except Exception:
            return ServiceResult.fail(f"Cart with id {cart_id} not found")
        except Exception as e:
            return ServiceResult.fail(f"Order creation failed: {str(e)}")
    
    def confirm(self, order_id: int) -> ServiceResult:
        """Confirm an order."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        return self.execute_workflow_trigger(order, 'confirm')
    
    def cancel(self, order_id: int, reason: str = "") -> ServiceResult:
        """Cancel an order."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        # Store cancellation reason if model supports it
        if hasattr(order, 'cancellation_reason'):
            order.cancellation_reason = reason
        
        return self.execute_workflow_trigger(order, 'cancel')
    
    def process(self, order_id: int) -> ServiceResult:
        """Start processing an order."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        return self.execute_workflow_trigger(order, 'start_processing')
    
    def ship(
        self,
        order_id: int,
        tracking_info: Optional[Dict] = None
    ) -> ServiceResult:
        """Mark order as shipped."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        # Store tracking info if model supports it
        if tracking_info and hasattr(order, 'tracking_number'):
            order.tracking_number = tracking_info.get('tracking_number')
            order.shipping_carrier = tracking_info.get('carrier')
        
        return self.execute_workflow_trigger(order, 'ship')
    
    def deliver(self, order_id: int) -> ServiceResult:
        """Mark order as delivered."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        return self.execute_workflow_trigger(order, 'deliver')
    
    def get_order_summary(self, order_id: int) -> ServiceResult:
        """Get detailed order summary."""
        order = self.get_by_id(order_id)
        if not order:
            return ServiceResult.fail(f"Order {order_id} not found")
        
        summary = {
            'id': order.id,
            'status': order.status,
            'customer': {
                'name': f"{order.first_name} {order.last_name}",
                'email': order.email,
                'address': f"{order.address}, {order.postal_code} {order.city}"
            },
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.get_cost())
                }
                for item in order.items.all()
            ],
            'total': float(order.get_total_cost()),
            'created': order.created,
            'updated': order.updated,
            'available_transitions': []
        }
        
        # Add workflow transitions if supported
        if isinstance(order, WorkflowMixin):
            summary['available_transitions'] = order.get_available_triggers()
        
        return ServiceResult.ok(summary)
    
    def list_by_status(self, status: OrderStatus) -> ServiceResult:
        """List orders by status."""
        orders = self.get_queryset().filter(status=status.value)
        return ServiceResult.ok(list(orders))


class CartService(BaseService):
    """
    Service for managing shopping carts.
    """
    
    from shop.models import ShopCart
    model_class = ShopCart
    
    def add_item(
        self,
        cart_id: int,
        product_id: int,
        quantity: int = 1
    ) -> ServiceResult:
        """Add a product to cart."""
        try:
            cart = self.get_by_id(cart_id)
            if not cart:
                return ServiceResult.fail(f"Cart {cart_id} not found")
            
            from product.models import Product
            product = Product.objects.get(id=product_id)
            
            if quantity <= 0:
                return ServiceResult.fail("Quantity must be positive")
            
            if product.stock < quantity:
                return ServiceResult.fail(
                    f"Insufficient stock for {product.name}"
                )
            
            cart.add_product(product, quantity)
            return ServiceResult.ok(cart, "Item added to cart")
            
        except Product.DoesNotExist:
            return ServiceResult.fail(f"Product {product_id} not found")
    
    def remove_item(self, cart_id: int, item_id: int) -> ServiceResult:
        """Remove an item from cart."""
        try:
            cart = self.get_by_id(cart_id)
            if not cart:
                return ServiceResult.fail(f"Cart {cart_id} not found")
            
            from shop.models import CartItem
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            
            return ServiceResult.ok(cart, "Item removed from cart")
            
        except CartItem.DoesNotExist:
            return ServiceResult.fail(f"Item {item_id} not found in cart")
    
    def get_cart_summary(self, cart_id: int) -> ServiceResult:
        """Get cart summary with totals."""
        cart = self.get_by_id(cart_id)
        if not cart:
            return ServiceResult.fail(f"Cart {cart_id} not found")
        
        items = cart.items.all()
        summary = {
            'id': cart.id,
            'items_count': items.count(),
            'items': [
                {
                    'id': item.id,
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.product.price),
                    'total': float(item.total_price)
                }
                for item in items
            ],
            'subtotal': sum(float(item.total_price) for item in items),
            'updated_at': cart.updated_at
        }
        
        return ServiceResult.ok(summary)
