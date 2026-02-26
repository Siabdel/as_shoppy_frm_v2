"""
Customer API Views

REST API endpoints for customer management.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Customer
from .serializers import CustomerSerializer, CustomerListSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing customers.
    
    Provides CRUD operations and additional actions for customer management.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['created_at', 'updated_at', 'user__date_joined']
    lookup_field = 'pk'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerSerializer
    
    def get_queryset(self):
        """Filter customers based on user permissions."""
        queryset = Customer.objects.all()
        
        # Filter by state
        state = self.request.query_params.get('state')
        if state:
            queryset = queryset.filter(state=state)
        
        # Filter by recognized status
        recognized = self.request.query_params.get('recognized')
        if recognized is not None:
            queryset = queryset.filter(recognized=recognized.lower() == 'true')
        
        return queryset.select_related('user').prefetch_related('orders')
    
    @action(detail=True, methods=['post'])
    def recognize(self, request, pk=None):
        """
        Mark a customer as recognized.
        
        This action transitions a customer from unrecognized/guest to recognized state.
        """
        customer = self.get_object()
        customer.recognized = True
        customer.state = 2  # REGISTERED
        customer.save()
        return Response(
            {'status': 'customer recognized', 'recognized': customer.recognized},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def set_guest(self, request, pk=None):
        """Set customer as guest."""
        customer = self.get_object()
        customer.state = 1  # GUEST
        customer.save()
        return Response(
            {'status': 'customer set as guest', 'state': customer.state},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get all orders for a customer."""
        customer = self.get_object()
        orders = customer.orders.all()
        return Response({
            'customer_id': customer.id,
            'order_count': orders.count(),
            'orders': [{'id': o.id, 'status': getattr(o, 'status', 'N/A')} for o in orders]
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get customer statistics."""
        total = Customer.objects.count()
        recognized = Customer.objects.filter(recognized=True).count()
        guests = Customer.objects.filter(state=1).count()  # GUEST
        registered = Customer.objects.filter(state=2).count()  # REGISTERED
        
        return Response({
            'total_customers': total,
            'recognized': recognized,
            'guests': guests,
            'registered': registered,
            'unrecognized': total - recognized
        })
