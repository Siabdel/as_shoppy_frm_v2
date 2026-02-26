"""
Quote Service Module

Handles business logic for quote (devis) management including
workflow operations and conversion to invoices.
"""

from typing import Dict, Any, Optional
from datetime import date

from django.db import transaction

from .base import BaseService, ServiceResult, ValidationError
from core.enums import QuoteStatus
from core.state_machine import QuoteWorkflow, WorkflowMixin


class QuoteService(BaseService):
    """
    Service for managing quotes and their lifecycle.
    Handles workflow transitions and invoice conversion.
    """
    
    from devis.models import Quote
    model_class = Quote
    workflow_class = QuoteWorkflow
    
    def __init__(self, user=None, context: Optional[Dict[str, Any]] = None):
        super().__init__(user, context)
    
    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Validate quote data."""
        errors = {}
        
        if not data.get('client_id'):
            errors['client'] = "Client is required"
        
        if not data.get('date_expiration'):
            errors['date_expiration'] = "Expiration date is required"
        elif data.get('date_expiration') < date.today():
            errors['date_expiration'] = "Expiration date must be in the future"
        
        if 'items' in data and not data['items']:
            errors['items'] = "Quote must have at least one item"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def perform_create(self, validated_data: Dict[str, Any]) -> Any:
        """Create quote with items."""
        items_data = validated_data.pop('items', [])
        
        # Handle client
        client_id = validated_data.pop('client_id', None)
        if client_id:
            from customer.models import Customer
            validated_data['client'] = Customer.objects.get(id=client_id)
        
        # Set creator
        if self.user:
            validated_data['created_by'] = self.user
        
        instance = super().perform_create(validated_data)
        
        # Create quote items
        from devis.models import QuoteItem
        for item_data in items_data:
            QuoteItem.objects.create(
                quote=instance,
                **item_data
            )
        
        # Calculate total
        self._recalculate_total(instance)
        
        return instance
    
    def perform_update(
        self,
        instance: Any,
        validated_data: Dict[str, Any]
    ) -> Any:
        """Update quote with items."""
        items_data = validated_data.pop('items', None)
        
        # Handle client
        client_id = validated_data.pop('client_id', None)
        if client_id:
            from customer.models import Customer
            validated_data['client'] = Customer.objects.get(id=client_id)
        
        instance = super().perform_update(instance, validated_data)
        
        # Update items if provided
        if items_data is not None:
            # Remove existing items
            instance.items.all().delete()
            
            # Create new items
            from devis.models import QuoteItem
            for item_data in items_data:
                QuoteItem.objects.create(
                    quote=instance,
                    **item_data
                )
            
            # Recalculate total
            self._recalculate_total(instance)
        
        return instance
    
    def _recalculate_total(self, quote: Any):
        """Recalculate quote total from items."""
        total = sum(
            item.quantity * item.price
            for item in quote.items.all()
        )
        quote.total_amount = total
        quote.save(update_fields=['total_amount'])
    
    def send(self, quote_id: int) -> ServiceResult:
        """Send quote to client."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        result = self.execute_workflow_trigger(quote, 'send')
        if result.is_ok:
            # Trigger email notification
            self._send_quote_email(quote)
        
        return result
    
    def accept(
        self,
        quote_id: int,
        accepted_by: Optional[Any] = None
    ) -> ServiceResult:
        """Mark quote as accepted."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        return self.execute_workflow_trigger(quote, 'accept')
    
    def reject(self, quote_id: int, reason: str = "") -> ServiceResult:
        """Reject a quote."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        if reason and hasattr(quote, 'rejection_reason'):
            quote.rejection_reason = reason
            quote.save(update_fields=['rejection_reason'])
        
        return self.execute_workflow_trigger(quote, 'reject')
    
    def expire(self, quote_id: int) -> ServiceResult:
        """Mark quote as expired."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        return self.execute_workflow_trigger(quote, 'expire')
    
    def convert_to_invoice(self, quote_id: int) -> ServiceResult:
        """Convert accepted quote to invoice."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        # Check if quote is accepted
        if quote.status != QuoteStatus.ACCEPTED.value:
            return ServiceResult.fail(
                "Only accepted quotes can be converted to invoices"
            )
        
        try:
            with transaction.atomic():
                # Import invoice service here to avoid circular imports
                from .invoice_service import InvoiceService
                invoice_service = InvoiceService(self.user, self.context)
                # Execute workflow transition
                wf_result = self.execute_workflow_trigger(
                    quote,
                    'convert_to_invoice'
                )
                if wf_result.is_fail:
                    return wf_result
                
                # Create invoice from quote
                invoice_data = {
                    'client_id': quote.client_id,
                    'total_amount': quote.total_amount,
                    'quote_source_id': quote.id,
                    'items': [
                        {
                            'product_id': item.product_id,
                            'quantity': item.quantity,
                            'price': item.price,
                            'tax': item.tax,
                            'rate': item.rate
                        }
                        for item in quote.items.all()
                    ]
                }
                
                inv_result = invoice_service.create(invoice_data)
                if inv_result.is_fail:
                    raise Exception(inv_result.message)
                
                invoice = inv_result.data
                
                # Link invoice to quote
                quote.invoice = invoice
                quote.save(update_fields=['invoice'])
                
                return ServiceResult.ok(
                    {'quote': quote, 'invoice': invoice},
                    "Quote converted to invoice successfully"
                )
                
        except Exception as e:
            return ServiceResult.fail(f"Conversion failed: {str(e)}")
    
    def duplicate(self, quote_id: int) -> ServiceResult:
        """Create a copy of an existing quote."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        try:
            from datetime import timedelta
            from django.utils import timezone
            
            new_data = {
                'client_id': quote.client_id,
                'date_expiration': timezone.now().date() + timedelta(days=30),
                'quote_terms': quote.quote_terms,
                'items': [
                    {
                        'product_id': item.product_id,
                        'quantity': item.quantity,
                        'price': item.price,
                        'tax': item.tax,
                        'rate': item.rate
                    }
                    for item in quote.items.all()
                ]
            }
            
            return self.create(new_data)
            
        except Exception as e:
            return ServiceResult.fail(f"Duplication failed: {str(e)}")
    
    def get_quote_summary(self, quote_id: int) -> ServiceResult:
        """Get detailed quote summary."""
        quote = self.get_by_id(quote_id)
        if not quote:
            return ServiceResult.fail(f"Quote {quote_id} not found")
        
        summary = {
            'id': quote.id,
            'numero': quote.numero,
            'status': quote.status,
            'client': {
                'id': quote.client_id,
                'name': str(quote.client)
                if hasattr(quote.client, '__str__')
                else None
            },
            'total_amount': float(quote.total_amount),
            'date_expiration': quote.date_expiration,
            'created_at': quote.created_at,
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.subtotal)
                }
                for item in quote.items.all()
            ],
            'available_transitions': []
        }
        
        if isinstance(quote, WorkflowMixin):
            summary['available_transitions'] = quote.get_available_triggers()
        
        return ServiceResult.ok(summary)
    
    def list_expired(self) -> ServiceResult:
        """List all expired quotes."""
        from django.utils import timezone
        quotes = self.get_queryset().filter(
            date_expiration__lt=timezone.now().date()
        ).exclude(status=QuoteStatus.EXPIRED.value)
        
        return ServiceResult.ok(list(quotes))
    
    def bulk_expire(self) -> ServiceResult:
        """Mark all past-due quotes as expired."""
        result = self.list_expired()
        if result.is_fail:
            return result
        
        expired_count = 0
        for quote in result.data:
            expire_result = self.expire(quote.id)
            if expire_result.is_ok:
                expired_count += 1
        
        return ServiceResult.ok(
            {'expired_count': expired_count},
            f"{expired_count} quotes marked as expired"
        )
    
    def _send_quote_email(self, quote: Any):
        """Send quote email notification."""
        # Implementation for email sending
        # This would integrate with Django's email system
        pass
