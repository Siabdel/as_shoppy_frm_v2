# -*- coding: utf-8 -*-
"""
Vues API pour CMagic Sport.
"""
from django.db import models
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import SportProduct
from .serializers import (
    SportProductSerializer,
    SportProductListSerializer,
    SportProductCreateSerializer,
)


class SportProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les produits sport.
    
    Endpoints:
    - GET /api/v1/cmagic-sport/products/ - Liste des produits
    - POST /api/v1/cmagic-sport/products/ - Créer un produit
    - GET /api/v1/cmagic-sport/products/{id}/ - Détail d'un produit
    - PUT /api/v1/cmagic-sport/products/{id}/ - Modifier un produit
    - DELETE /api/v1/cmagic-sport/products/{id}/ - Supprimer un produit
    """
    
    queryset = SportProduct.objects.all()
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'list':
            return SportProductListSerializer
        if self.action == 'create':
            return SportProductCreateSerializer
        return SportProductSerializer
    
    def get_queryset(self):
        """Filtrage personnalisé du queryset."""
        queryset = super().get_queryset()
        
        # Filtres par marque
        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)
        
        # Filtres par type de produit
        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filtres par genre
        gender = self.request.query_params.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Filtres par taille EU
        size_eu = self.request.query_params.get('size_eu')
        if size_eu:
            queryset = queryset.filter(size_eu=size_eu)
        
        # Filtres par couleur
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(color__icontains=color)
        
        # Filtres par matériau
        material = self.request.query_params.get('material')
        if material:
            queryset = queryset.filter(material=material)
        
        # Filtre en stock uniquement
        in_stock_only = self.request.query_params.get('in_stock_only')
        if in_stock_only and in_stock_only.lower() == 'true':
            queryset = queryset.filter(in_stock=True, stock__gt=0)
        
        # Filtre édition limitée
        limited_only = self.request.query_params.get('limited_only')
        if limited_only and limited_only.lower() == 'true':
            queryset = queryset.filter(is_limited_edition=True)
        
        # Recherche textuelle
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(model_name__icontains=search) |
                models.Q(style_code__icontains=search)
            )
        
        return queryset.prefetch_related('polymorphic_ctype')
    
    @action(detail=True, methods=['get'])
    def availability(self, request, slug=None):
        """Retourne la disponibilité d'un produit spécifique."""
        product = self.get_object()
        availability = product.get_availability()
        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'is_available': availability.is_available,
            'quantity': availability.quantity,
            'message': availability.message,
        })
    
    @action(detail=False, methods=['get'])
    def brands(self, request):
        """Retourne la liste des marques disponibles depuis les spécifications."""
        from product.models import ProductSpecificationValue, ProductSpecification
        from django.contrib.contenttypes.models import ContentType
        
        # Get SportProduct content type
        sport_ct = ContentType.objects.get_for_model(SportProduct)
        
        # Get brands from ProductSpecificationValue where specification name is 'Brand'
        brand_spec = ProductSpecification.objects.filter(name='Brand').first()
        if brand_spec:
            brand_values = ProductSpecificationValue.objects.filter(
                product_content_type=sport_ct,
                specification=brand_spec
            ).values_list('value', flat=True).distinct()
            brands = [{'value': b, 'label': b} for b in brand_values]
        else:
            # Fallback: get unique brand values directly from products
            brands = SportProduct.objects.exclude(
                brand=''
            ).values_list('brand', flat=True).distinct()
            brands = [{'value': b, 'label': b} for b in brands]
        
        return Response(brands)
    
    @action(detail=False, methods=['get'])
    def sizes(self, request):
        """Retourne la liste des tailles disponibles."""
        # Get unique sizes from available_sizes field
        all_sizes = SportProduct.objects.exclude(
            available_sizes=''
        ).values_list('available_sizes', flat=True).distinct()
        
        # Parse and deduplicate sizes
        size_set = set()
        for sizes_str in all_sizes:
            if sizes_str:
                for size in sizes_str.split(','):
                    size = size.strip()
                    if size:
                        size_set.add(size)
        
        return Response(sorted(list(size_set)))
    
    @action(detail=False, methods=['get'])
    def colors(self, request):
        """Retourne la liste des couleurs disponibles."""
        colors = SportProduct.objects.exclude(
            color=''
        ).values_list('color', flat=True).distinct()
        return Response(list(colors))


class CMagicSportCatalogView(generics.ListAPIView):
    """
    Vue catalogue pour CMagic Sport.
    
    URL: /cmagic-sport/
    """
    
    serializer_class = SportProductListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Retourne les produits sport avec les filtres."""
        queryset = SportProduct.objects.all()
        
        # Filtre par marque
        brand = self.request.query_params.get('brand')
        if brand:
            brands = brand.split(',')
            queryset = queryset.filter(brand__in=brands)
        
        # Filtre par type
        product_type = self.request.query_params.get('product_type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filtre par taille
        size = self.request.query_params.get('size')
        if size:
            queryset = queryset.filter(size_eu=size)
        
        # Filtre par couleur
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(color__icontains=color)
        
        # Filtre prix min/max
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # En stock uniquement
        in_stock = self.request.query_params.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(in_stock=True, stock__gt=0)
        
        return queryset.prefetch_related('polymorphic_ctype')


class SportProductDetailView(generics.RetrieveAPIView):
    """
    Vue détail pour un produit sport.
    
    URL: /cmagic-sport/product/<slug:slug>/
    """
    
    serializer_class = SportProductSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    queryset = SportProduct.objects.all()


# ============================================
# Template Views - Vitrine Client
# ============================================

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages


class CatalogView(TemplateView):
    """
    Vue catalogue pour CMagic Sport.
    
    URL: /cmagic-sport/
    """
    template_name = 'cmagic_sport/catalog.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products with filters
        products = SportProduct.objects.filter(is_active=True)
        
        # Apply filters
        brand = self.request.GET.get('brand')
        if brand:
            products = products.filter(brand=brand)
        
        product_type = self.request.GET.get('product_type')
        if product_type:
            products = products.filter(product_type=product_type)
        
        gender = self.request.GET.get('gender')
        if gender:
            products = products.filter(gender=gender)
        
        in_stock = self.request.GET.get('in_stock')
        if in_stock and in_stock.lower() == 'true':
            products = products.filter(in_stock=True, stock__gt=0)
        
        limited_only = self.request.GET.get('limited_only')
        if limited_only and limited_only.lower() == 'true':
            products = products.filter(is_limited_edition=True)
        
        search = self.request.GET.get('search')
        if search:
            products = products.filter(
                models.Q(name__icontains=search) |
                models.Q(description__icontains=search) |
                models.Q(model_name__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(products, 12)
        page = self.request.GET.get('page', 1)
        
        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)
        
        context['products'] = products_page
        
        # Get brands from specifications or products
        from product.models import ProductSpecificationValue, ProductSpecification
        from django.contrib.contenttypes.models import ContentType
        
        sport_ct = ContentType.objects.get_for_model(SportProduct)
        
        # Get unique brand values from ProductSpecificationValue
        brand_spec = ProductSpecification.objects.filter(name='Brand').first()
        if brand_spec:
            brand_values = ProductSpecificationValue.objects.filter(
                product_content_type=sport_ct,
                specification=brand_spec
            ).values_list('value', flat=True).distinct()
            context['brands'] = [(b, b) for b in brand_values]
        else:
            # Fallback: get unique brand values directly from products
            brand_values = SportProduct.objects.exclude(
                brand=''
            ).values_list('brand', flat=True).distinct()
            context['brands'] = [(b, b) for b in brand_values]
        
        # Get product types from ProductType model
        from product.models import ProductType
        product_types = ProductType.objects.filter(is_active=True)
        context['product_types'] = [(pt.id, pt.name) for pt in product_types]
        
        return context


class ProductDetailView(DetailView):
    """
    Vue détail pour un produit sport.
    
    URL: /cmagic-sport/product/<slug:slug>/
    """
    model = SportProduct
    template_name = 'cmagic_sport/product_detail.html'
    context_object_name = 'product'
    lookup_field = 'slug'
    
    def get_object(self):
        return get_object_or_404(
            SportProduct.objects.prefetch_related('polymorphic_ctype'),
            slug=self.kwargs['slug'],
            is_active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related products (same brand or type)
        product = self.object
        related = SportProduct.objects.filter(
            models.Q(brand=product.brand) | models.Q(product_type=product.product_type)
        ).exclude(id=product.id).filter(is_active=True)[:4]
        
        context['related_products'] = related
        context['available_sizes'] = ['38', '39', '40', '41', '42', '43', '44', '45']
        
        return context


class CartView(TemplateView):
    """
    Vue panier.
    
    URL: /cmagic-sport/cart/
    """
    template_name = 'cmagic_sport/cart.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cart from session (mock for now)
        cart_items = []
        cart_total = 0
        
        # In a real app, this would get from session/database
        # For demo, we'll show empty cart
        context['cart_items'] = cart_items
        context['cart'] = {
            'get_subtotal': 0,
            'get_tax': 0,
            'get_total': 0,
            'get_total_price': 0,
        }
        
        return context


class CheckoutView(TemplateView):
    """
    Vue checkout/paiement.
    
    URL: /cmagic-sport/checkout/
    """
    template_name = 'cmagic_sport/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock cart items for demo
        context['cart_items'] = []
        context['cart'] = {
            'get_subtotal': 0,
            'get_tax': 0,
            'get_total': 0,
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Process checkout
        # In a real app, this would handle payment processing
        return redirect('cmagic_sport:checkout_success')


class CheckoutSuccessView(TemplateView):
    """
    Vue confirmation de commande.
    
    URL: /cmagic-sport/checkout/success/
    """
    template_name = 'cmagic_sport/checkout_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Mock order data for demo
        context['order'] = {
            'order_number': 'CMG-2024-001234',
            'created_at': timezone.now(),
            'customer_email': self.request.user.email if self.request.user.is_authenticated else 'client@email.com',
            'payment_method': 'Carte bancaire',
            'delivery_method': 'Livraison standard',
            'total': 149.99,
            'subtotal': 129.99,
            'tax': 20.00,
        }
        
        return context


# Import timezone for the success view
from django.utils import timezone