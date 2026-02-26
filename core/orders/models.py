"""
Unified Order Models Module

Consolidates order-related models with workflow support,
enums integration, and service layer compatibility.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings

from core.enums import OrderStatus, PaymentStatus, ChoiceEnumField
from core.state_machine import WorkflowMixin
from product import models as pro_models


class Order(WorkflowMixin, models.Model):
    """
    Unified Order model with workflow support.
    
    Combines functionality from the simple Order model and
    integrates with the state machine for lifecycle management.
    """
    
    # Customer Information
    first_name = models.CharField(max_length=60, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=60, verbose_name=_("Last Name"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(
        max_length=20, blank=True, verbose_name=_("Phone")
    )
    
    # Shipping Address
    address = models.CharField(max_length=150, verbose_name=_("Address"))
    address_line2 = models.CharField(
        max_length=150, blank=True, verbose_name=_("Address Line 2")
    )
    postal_code = models.CharField(
        max_length=30, verbose_name=_("Postal Code")
    )
    city = models.CharField(max_length=100, verbose_name=_("City"))
    country = models.CharField(
        max_length=100, default="France", verbose_name=_("Country")
    )
    
    # Billing Address (optional, defaults to shipping)
    billing_address = models.CharField(
        max_length=150, blank=True, verbose_name=_("Billing Address")
    )
    billing_postal_code = models.CharField(
        max_length=30, blank=True, verbose_name=_("Billing Postal Code")
    )
    billing_city = models.CharField(
        max_length=100, blank=True, verbose_name=_("Billing City")
    )
    
    # Order Status with Workflow
    status = ChoiceEnumField(
        enum_type=OrderStatus,
        default=OrderStatus.PENDING,
        verbose_name=_("Status")
    )
    
    # Payment Information
    payment_status = ChoiceEnumField(
        enum_type=PaymentStatus,
        default=PaymentStatus.PENDING,
        verbose_name=_("Payment Status")
    )
    paid = models.BooleanField(default=False, verbose_name=_("Paid"))
    paid_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Paid At")
    )
    
    # Shipping Information
    shipping_method = models.CharField(
        max_length=100, blank=True, verbose_name=_("Shipping Method")
    )
    shipping_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Shipping Cost")
    )
    tracking_number = models.CharField(
        max_length=100, blank=True, verbose_name=_("Tracking Number")
    )
    shipping_carrier = models.CharField(
        max_length=100, blank=True, verbose_name=_("Shipping Carrier")
    )
    shipped_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Shipped At")
    )
    delivered_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Delivered At")
    )
    
    # Financial Summary
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Subtotal")
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Tax Amount")
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Discount Amount")
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Total")
    )
    
    # Timestamps
    created = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created")
    )
    updated = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated")
    )
    
    # User Relations
    customer = models.ForeignKey(
        'customer.Customer',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders',
        verbose_name=_("Customer")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders',
        verbose_name=_("User")
    )
    
    # Cancellation
    cancellation_reason = models.TextField(
        blank=True, verbose_name=_("Cancellation Reason")
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Cancelled At")
    )
    
    # Notes
    customer_notes = models.TextField(
        blank=True, verbose_name=_("Customer Notes")
    )
    internal_notes = models.TextField(
        blank=True, verbose_name=_("Internal Notes")
    )
    
    # Workflow Configuration
    _state_field = 'status'
    
    class Meta:
        ordering = ('-created',)
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        indexes = [
            models.Index(fields=['status', 'created']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['paid', 'status']),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate totals."""
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate order totals from items."""
        self.subtotal = sum(
            item.get_subtotal() for item in self.items.all()
        )
        self.total = (
            self.subtotal +
            self.shipping_cost +
            self.tax_amount -
            self.discount_amount
        )
    
    def get_total_cost(self):
        """Legacy method for backward compatibility."""
        return self.total
    
    def get_subtotal(self):
        """Get order subtotal."""
        return self.subtotal
    
    def get_item_count(self):
        """Get total number of items."""
        return sum(item.quantity for item in self.items.all())
    
    # Workflow Methods
    def can_confirm(self):
        """Check if order can be confirmed."""
        return self.status == OrderStatus.PENDING.value
    
    def can_cancel(self):
        """Check if order can be cancelled."""
        return self.status in [
            OrderStatus.PENDING.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.ON_HOLD.value
        ]
    
    def can_ship(self):
        """Check if order can be shipped."""
        return self.status == OrderStatus.PROCESSING.value
    
    def can_deliver(self):
        """Check if order can be marked as delivered."""
        return self.status == OrderStatus.SHIPPED.value


class OrderItem(models.Model):
    """
    Unified Order Item model.
    
    Represents a product line in an order with full pricing details.
    """
    
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name=_("Order")
    )
    product = models.ForeignKey(
        pro_models.Product,
        related_name='order_items',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Product")
    )
    
    # Product Details (snapshot at time of order)
    product_name = models.CharField(
        max_length=255, verbose_name=_("Product Name")
    )
    product_sku = models.CharField(
        max_length=100, blank=True, verbose_name=_("SKU")
    )
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_("Unit Price")
    )
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Original Price")
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name=_("Quantity")
    )
    
    # Discounts
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Discount Amount")
    )
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0, verbose_name=_("Discount %")
    )
    
    # Tax
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0, verbose_name=_("Tax Rate %")
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Tax Amount")
    )
    
    # Totals
    line_total = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0, verbose_name=_("Line Total")
    )
    
    class Meta:
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Calculate line totals before saving."""
        self.calculate_line_total()
        super().save(*args, **kwargs)
    
    def calculate_line_total(self):
        """Calculate the line total."""
        subtotal = self.price * self.quantity
        discount = self.discount_amount * self.quantity
        self.line_total = subtotal - discount + self.tax_amount
    
    def get_cost(self):
        """Legacy method for backward compatibility."""
        return self.line_total
    
    def get_subtotal(self):
        """Get item subtotal (price * quantity)."""
        return self.price * self.quantity
    
    def get_discount(self):
        """Get total discount for this line."""
        return self.discount_amount * self.quantity


class OrderPayment(models.Model):
    """
    Order Payment model.
    
    Tracks payments made against an order.
    """
    
    order = models.ForeignKey(
        Order,
        related_name='payments',
        on_delete=models.CASCADE,
        verbose_name=_("Order")
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name=_("Amount")
    )
    payment_method = models.CharField(
        max_length=50,
        verbose_name=_("Payment Method")
    )
    transaction_id = models.CharField(
        max_length=255, blank=True,
        verbose_name=_("Transaction ID")
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
            ('refunded', _('Refunded')),
        ],
        default='pending',
        verbose_name=_("Status")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At")
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completed At")
    )
    
    class Meta:
        verbose_name = _("Order Payment")
        verbose_name_plural = _("Order Payments")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.id} for Order {self.order_id}"
    
    def mark_completed(self):
        """Mark payment as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Update order payment status
        self.order.paid = True
        self.order.paid_at = timezone.now()
        self.order.payment_status = PaymentStatus.CAPTURED
        self.order.save()
    
    def mark_failed(self, reason=""):
        """Mark payment as failed."""
        self.status = 'failed'
        self.save()
        
        self.order.payment_status = PaymentStatus.FAILED
        self.order.save()


class OrderStatusHistory(models.Model):
    """
    Order Status History model.
    
    Tracks all status changes for audit purposes.
    """
    
    order = models.ForeignKey(
        Order,
        related_name='status_history',
        on_delete=models.CASCADE,
        verbose_name=_("Order")
    )
    from_status = models.CharField(
        max_length=50, verbose_name=_("From Status")
    )
    to_status = models.CharField(max_length=50, verbose_name=_("To Status"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name=_("Changed By")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At")
    )
    
    class Meta:
        verbose_name = _("Order Status History")
        verbose_name_plural = _("Order Status Histories")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_status} -> {self.to_status}"
