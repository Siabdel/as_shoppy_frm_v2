from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from .models import Quote, QuoteItem, StatutDevis
from .serializers import (
    QuoteSerializer, QuoteListSerializer,
    QuoteItemSerializer, QuoteCreateUpdateSerializer
)


class QuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quotes (devis).
    
    Provides CRUD operations and additional actions for quote management.
    """
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'client__user__username', 'quote_terms']
    ordering_fields = ['created_at', 'total_amount', 'date_expiration']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuoteCreateUpdateSerializer
        return QuoteSerializer
    
    def get_queryset(self):
        """Filter quotes based on query params."""
        queryset = Quote.objects.all()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by completed
        completed = self.request.query_params.get('completed')
        if completed is not None:
            queryset = queryset.filter(completed=completed.lower() == 'true')
        
        return queryset.select_related('client', 'created_by')
    
    def perform_create(self, serializer):
        """Set the created_by field to current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def convert_to_invoice(self, request, pk=None):
        """Convert an accepted quote to an invoice."""
        quote = self.get_object()
        if quote.status == StatutDevis.ACCEPTE.code:
            try:
                invoice = quote.convertir_en_facture()
                return Response(
                    {'message': f'Devis converti en facture {invoice.numero}'},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Seuls les devis acceptés peuvent être convertis en factures.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        """Mark quote as sent."""
        quote = self.get_object()
        quote.marquer_comme_envoye()
        return Response(
            {'status': 'sent', 'numero': quote.numero},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_accepted(self, request, pk=None):
        """Mark quote as accepted."""
        quote = self.get_object()
        quote.marquer_comme_accepte()
        return Response(
            {'status': 'accepted', 'numero': quote.numero},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_rejected(self, request, pk=None):
        """Mark quote as rejected."""
        quote = self.get_object()
        quote.marquer_comme_refuse()
        return Response(
            {'status': 'rejected', 'numero': quote.numero},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get all items for a quote."""
        quote = self.get_object()
        items = quote.items.all()
        serializer = QuoteItemSerializer(items, many=True)
        return Response({
            'quote_numero': quote.numero,
            'item_count': items.count(),
            'items': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get quote statistics."""
        from django.db.models import Count, Sum
        
        total = Quote.objects.count()
        by_status = Quote.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        total_amount = Quote.objects.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        completed = Quote.objects.filter(completed=True).count()
        
        return Response({
            'total_quotes': total,
            'by_status': list(by_status),
            'total_amount': str(total_amount),
            'completed': completed,
            'pending': total - completed
        })


class QuoteItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quote items.
    """
    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter items by quote."""
        queryset = QuoteItem.objects.all()
        quote_id = self.request.query_params.get('quote')
        if quote_id:
            queryset = queryset.filter(quote_id=quote_id)
        return queryset.select_related('quote', 'product')
