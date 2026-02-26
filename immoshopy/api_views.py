"""
ImmoProduct API Views

REST API endpoints for real estate product management.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import ImmoProduct
from .serializers import ImmoProductSerializer, ImmoProductListSerializer


class ImmoProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing real estate products (ImmoProduct).
    
    Provides CRUD operations and additional actions for property management.
    """
    queryset = ImmoProduct.objects.all()
    serializer_class = ImmoProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['product_name', 'name', 'description', 'slug']
    ordering_fields = ['created_at', 'updated_at', 'price', 'name']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ImmoProductListSerializer
        return ImmoProductSerializer
    
    def get_queryset(self):
        """Filter products based on query parameters."""
        queryset = ImmoProduct.objects.all()
        
        # Filter by availability
        available = self.request.query_params.get('available')
        if available is not None:
            queryset = queryset.filter(available=available.lower() == 'true')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by project
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset.select_related('project', 'category')
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, slug=None):
        """Toggle product availability status."""
        product = self.get_object()
        product.available = not product.available
        product.save()
        return Response(
            {'slug': product.slug, 'available': product.available},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, slug=None):
        """Update product stock quantity."""
        product = self.get_object()
        new_stock = request.data.get('stock')
        if new_stock is not None:
            try:
                new_stock = int(new_stock)
                product.stock = new_stock
                product.save()
                return Response(
                    {'slug': product.slug, 'stock': product.stock, 'in_stock': product.in_stock},
                    status=status.HTTP_200_OK
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid stock value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Stock value is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def images(self, request, slug=None):
        """Get all images for a product."""
        product = self.get_object()
        images = product.images.all()
        return Response({
            'product_slug': product.slug,
            'product_name': product.product_name or product.name,
            'image_count': images.count(),
            'images': [
                {
                    'id': img.id,
                    'title': img.title,
                    'image_url': request.build_absolute_uri(img.image.url) if img.image else None,
                    'thumbnail': request.build_absolute_uri(img.thumbnail_path) if hasattr(img, 'thumbnail_path') and img.thumbnail_path else None,
                }
                for img in images
            ]
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get real estate product statistics."""
        total = ImmoProduct.objects.count()
        available = ImmoProduct.objects.filter(available=True).count()
        out_of_stock = ImmoProduct.objects.filter(stock=0).count()
        
        # Price statistics
        from django.db.models import Avg, Min, Max
        price_stats = ImmoProduct.objects.aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        return Response({
            'total_products': total,
            'available': available,
            'unavailable': total - available,
            'out_of_stock': out_of_stock,
            'price_statistics': price_stats
        })
    
    @action(detail=False, methods=['get'])
    def by_project(self, request):
        """Get products grouped by project."""
        from django.db.models import Count
        from project.models import Project
        
        projects = Project.objects.annotate(
            product_count=Count('product')
        ).values('id', 'name', 'product_count')
        
        return Response(list(projects))
