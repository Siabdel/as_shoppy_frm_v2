# product/api_views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Product, ProductImage, ProductType, ProductSpecification
from .serializers import (
    ProductSerializer, ProductListSerializer, 
    ProductImageSerializer, ProductTypeSerializer,
    ProductSpecificationSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    
    Provides CRUD operations and additional actions for product management.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'slug', 'product_code']
    ordering_fields = ['created_at', 'updated_at', 'name', 'price']
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save()

    def get_queryset(self):
        """Filter products based on query params."""
        queryset = Product.objects.all()
        
        # Filter by project
        project_slug = self.request.query_params.get('project')
        if project_slug:
            queryset = queryset.filter(project__slug=project_slug)
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by availability
        available = self.request.query_params.get('available')
        if available is not None:
            queryset = queryset.filter(available=available.lower() == 'true')
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.select_related('project', 'category')

    @action(detail=True, methods=['post'])
    def add_image(self, request, slug=None):
        """Add an image to a product."""
        product = self.get_object()
        serializer = ProductImageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def remove_image(self, request, slug=None):
        """Remove an image from a product."""
        product = self.get_object()
        image_id = request.data.get('image_id')
        if image_id:
            image = get_object_or_404(ProductImage, id=image_id, product=product)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Image ID is required'}, 
            status=status.HTTP_400_BAD_REQUEST
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
                product.in_stock = new_stock > 0
                product.save()
                return Response(
                    {'stock': product.stock, 'in_stock': product.in_stock}, 
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

    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, slug=None):
        """Toggle product availability."""
        product = self.get_object()
        product.available = not product.available
        product.save()
        return Response(
            {'available': product.available}, 
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, slug=None):
        """Update product price."""
        product = self.get_object()
        price = request.data.get('price')
        if price is not None:
            try:
                price = float(price)
                product.price = price
                product.save()
                return Response(
                    {'price': str(product.price)}, 
                    status=status.HTTP_200_OK
                )
            except ValueError:
                return Response(
                    {'error': 'Invalid price value'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Price value is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get product statistics."""
        from django.db.models import Count, Avg
        
        total = Product.objects.count()
        available = Product.objects.filter(available=True).count()
        in_stock = Product.objects.filter(in_stock=True).count()
        active = Product.objects.filter(is_active=True).count()
        
        avg_price = Product.objects.filter(price__gt=0).aggregate(
            avg_price=Avg('price')
        )['avg_price'] or 0
        
        # Products by status
        status_counts = Product.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        return Response({
            'total_products': total,
            'available': available,
            'in_stock': in_stock,
            'active': active,
            'unavailable': total - available,
            'average_price': round(float(avg_price), 2),
            'by_status': list(status_counts)
        })


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product images.
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter images by product."""
        queryset = ProductImage.objects.all()
        product_slug = self.request.query_params.get('product')
        if product_slug:
            queryset = queryset.filter(product__slug=product_slug)
        return queryset.select_related('product')


class ProductTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for product types (read-only).
    """
    queryset = ProductType.objects.all()
    serializer_class = ProductTypeSerializer
    permission_classes = [IsAuthenticated]


class ProductSpecificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for product specifications (read-only).
    """
    queryset = ProductSpecification.objects.all()
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsAuthenticated]
