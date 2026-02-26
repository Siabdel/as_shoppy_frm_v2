"""
Invoice Service Module

Handles business logic for invoice management including
workflow operations and payment tracking.
"""

from typing import Dict, Any, Optional
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .base import BaseService, ServiceResult, ValidationError
from core.enums import InvoiceStatus
from core.state_machine import InvoiceWorkflow, WorkflowMixin


class InvoiceService(BaseService):
    """
    Service for managing invoices and their lifecycle.
    Handles workflow transitions and payment recording.
    """
    
    from invoice.models import Invoice
    model_class = Invoice
    workflow_class = InvoiceWorkflow
    
    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Validate invoice data."""
        errors = {}
        
        if not data.get('client_id'):
            errors['client'] = "Client is required"
        
        if 'items' in data and not data['items']:
            errors['items'] = "Invoice must have at least one item"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def perform_create(self, validated_data: Dict[str, Any]) -> Any:
        """Create invoice with items."""
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
        
        # Create invoice items
        from invoice.models import InvoiceItem
        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=instance,
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
        """Update invoice with items."""
        items_data = validated_data.pop('items', None)
        
        # Handle client
        client_id = validated_data.pop('client_id', None)
        if client_id:
            from customer.models import Customer
            validated_data['client'] = Customer.objects.get(id=client_id)
        
        instance = super().perform_update(instance, validated_data)
        
        # Update items if provided
        if items_data is not None:
            instance.items.all().delete()
            
            from invoice.models import InvoiceItem
            for item_data in items_data:
                InvoiceItem.objects.create(
                    invoice=instance,
                    **item_data
                )
            
            self._recalculate_total(instance)
        
        return instance
    
    def _recalculate_total(self, invoice: Any):
        """Recalculate invoice total from items."""
        total = sum(
            item.quantity * item.price
            for item in invoice.items.all()
        )
        invoice.total_amount = total
        invoice.save(update_fields=['total_amount'])
    
    def approve(self, invoice_id: int) -> ServiceResult:
        """Approve a draft invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        return self.execute_workflow_trigger(invoice, 'approve')
    
    def send(self, invoice_id: int) -> ServiceResult:
        """Send invoice to client."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        result = self.execute_workflow_trigger(invoice, 'send')
        if result.is_ok:
            self._send_invoice_email(invoice)
        
        return result
    
    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        payment_method: str = "",
        reference: str = ""
    ) -> ServiceResult:
        """Record a payment for an invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        try:
            with transaction.atomic():
                # Create payment record
                from invoice.models import Payment
                Payment.objects.create(
                    invoice=invoice,
                    amount=amount,
                    payment_method=payment_method,
                    reference=reference,
                    created_by=self.user
                )
                
                # Update invoice status
                total_paid = sum(p.amount for p in invoice.payments.all())
                
                if total_paid >= invoice.total_amount:
                    result = self.execute_workflow_trigger(
                        invoice,
                        'record_payment'
                    )
                else:
                    result = self.execute_workflow_trigger(
                        invoice,
                        'record_partial_payment'
                    )
                
                if result.is_fail:
                    raise Exception(result.message)
                
                return ServiceResult.ok(
                    invoice,
                    f"Payment of {amount} recorded successfully"
                )
                
        except Exception as e:
            return ServiceResult.fail(f"Payment recording failed: {str(e)}")
    
    def mark_overdue(self, invoice_id: int) -> ServiceResult:
        """Mark invoice as overdue."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        return self.execute_workflow_trigger(invoice, 'mark_overdue')
    
    def dispute(self, invoice_id: int, reason: str = "") -> ServiceResult:
        """Mark invoice as disputed."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        if reason and hasattr(invoice, 'dispute_reason'):
            invoice.dispute_reason = reason
            invoice.save(update_fields=['dispute_reason'])
        
        return self.execute_workflow_trigger(invoice, 'dispute')
    
    def resolve_dispute(self, invoice_id: int) -> ServiceResult:
        """Resolve a disputed invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        return self.execute_workflow_trigger(invoice, 'resolve_dispute')
    
    def cancel(self, invoice_id: int, reason: str = "") -> ServiceResult:
        """Cancel an invoice."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        if reason and hasattr(invoice, 'cancellation_reason'):
            invoice.cancellation_reason = reason
            invoice.save(update_fields=['cancellation_reason'])
        
        return self.execute_workflow_trigger(invoice, 'cancel')
    
    def get_invoice_summary(self, invoice_id: int) -> ServiceResult:
        """Get detailed invoice summary."""
        invoice = self.get_by_id(invoice_id)
        if not invoice:
            return ServiceResult.fail(f"Invoice {invoice_id} not found")
        
        total_paid = sum(
            p.amount for p in invoice.payments.all()
        ) if hasattr(invoice, 'payments') else Decimal('0')
        
        summary = {
            'id': invoice.id,
            'numero': invoice.numero,
            'status': invoice.status,
            'client': {
                'id': invoice.client_id,
                'name': str(invoice.client)
            },
            'total_amount': float(invoice.total_amount),
            'total_paid': float(total_paid),
            'balance_due': float(invoice.total_amount - total_paid),
            'created_at': invoice.created_at,
            'expiration_date': invoice.expiration_date,
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.price),
                    'subtotal': float(item.quantity * item.price)
                }
                for item in invoice.items.all()
            ],
            'available_transitions': []
        }
        
        if isinstance(invoice, WorkflowMixin):
            summary['available_transitions'] = invoice.get_available_triggers()
        
        return ServiceResult.ok(summary)
    
    def list_overdue(self) -> ServiceResult:
        """List all overdue invoices."""
        invoices = self.get_queryset().filter(
            expiration_date__lt=timezone.now(),
            status__in=[
                InvoiceStatus.PENDING.value,
                InvoiceStatus.PARTIALLY_PAID.value
            ]
        )
        return ServiceResult.ok(list(invoices))
    
    def bulk_mark_overdue(self) -> ServiceResult:
        """Mark all past-due invoices as overdue."""
        result = self.list_overdue()
        if result.is_fail:
            return result
        
        overdue_count = 0
        for invoice in result.data:
            overdue_result = self.mark_overdue(invoice.id)
            if overdue_result.is_ok:
                overdue_count += 1
        
        return ServiceResult.ok(
            {'overdue_count': overdue_count},
            f"{overdue_count} invoices marked as overdue"
        )
    
    def _send_invoice_email(self, invoice: Any):
        """Send invoice email notification."""
        pass
