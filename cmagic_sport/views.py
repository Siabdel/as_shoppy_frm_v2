# -*- coding: utf-8 -*-
"""
Vues API pour CMagic Sport.
"""
from django.db import models
from django.contrib.auth.mixins import LoginRequiredMixin
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
        
        # Get related products (same product type)
        product = self.object
        related = SportProduct.objects.filter(
            models.Q(product_type=product.product_type)
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
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - display the cart."""
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - add/remove items from cart."""
        cart = request.session.get('cart', {})
        
        # Handle add to cart
        if 'product_id' in request.POST:
            product_id = request.POST.get('product_id')
            size = request.POST.get('size', '')
            quantity = int(request.POST.get('quantity', 1))
            
            # Get product details
            from .models import SportProduct
            product = SportProduct.objects.filter(id=product_id).first()
            if product:
                item_key = f"{product_id}_{size}" if size else str(product_id)
                
                if item_key in cart:
                    cart[item_key]['quantity'] += quantity
                else:
                    cart[item_key] = {
                        'product_id': product_id,
                        'name': product.name,
                        'size': size,
                        'quantity': quantity,
                        'price': float(product.price),
                        'slug': product.slug,
                    }
                
                request.session['cart'] = cart
                request.session.modified = True
        
        # Handle remove item
        elif 'remove' in request.POST:
            item_id = request.POST.get('remove')
            if item_id in cart:
                del cart[item_id]
                request.session['cart'] = cart
                request.session.modified = True
        
        # Handle update quantity
        elif 'update_quantity' in request.POST:
            item_id = request.POST.get('item_id')
            quantity = int(request.POST.get('quantity', 1))
            if item_id in cart:
                if quantity > 0:
                    cart[item_id]['quantity'] = quantity
                else:
                    del cart[item_id]
                request.session['cart'] = cart
                request.session.modified = True
        
        # Redirect back to cart
        from django.shortcuts import redirect
        return redirect('cmagic_sport:cart')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cart from session
        request = self.request
        cart = request.session.get('cart', {})
        cart_items = []
        cart_total = 0
        
        # Build cart items list
        for item_key, item_data in cart.items():
            price = item_data.get('price', 0)
            quantity = item_data.get('quantity', 1)
            item_total = price * quantity
            item_data['get_total_price'] = item_total
            item_data['item_key'] = item_key
            cart_items.append(item_data)
            cart_total += item_total
        
        # Calculate totals
        tax_rate = 0.20  # 20% VAT
        tax = cart_total * tax_rate
        total = cart_total + tax
        
        context['cart_items'] = cart_items
        context['cart'] = {
            'get_subtotal': cart_total,
            'get_tax': tax,
            'get_total': total,
            'get_total_price': total,
        }
        
        return context


class CheckoutView(LoginRequiredMixin, TemplateView):
    """
    Vue checkout/paiement.
    
    URL: /cmagic-sport/checkout/
    """
    template_name = 'cmagic_sport/checkout.html'
    login_url = '/accounts/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get cart from session
        from core.cart.cart import Cart
        cart = Cart(self.request)
        
        # Get cart items
        cart_items = []
        cart_total = 0
        
        if hasattr(cart, 'cart') and cart.cart:
            try:
                for item in cart.cart.item_set.all():
                    item_data = {
                        'product': item.product,
                        'quantity': item.quantity,
                        'unit_price': item.unit_price,
                        'total_price': item.total_price,
                    }
                    cart_items.append(item_data)
                    cart_total += item.total_price
            except Exception:
                pass
        
        # Calculate totals
        tax_rate = 0.20  # 20% VAT
        tax = cart_total * tax_rate
        total = cart_total + tax
        
        context['cart_items'] = cart_items
        context['cart'] = {
            'get_subtotal': cart_total,
            'get_tax': tax,
            'get_total': total,
            'get_total_price': total,
        }
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Process checkout - create Order in database
        from core.cart.cart import Cart
        from django.utils import timezone
        import uuid
        
        cart = Cart(request)
        
        # Get or create customer
        customer = None
        if hasattr(request.user, 'customer'):
            customer = request.user.customer
        else:
            # Try to find by email
            customer = Customer.objects.filter(
                Q(created_by__email=request.user.email) |
                Q(email=request.user.email)
            ).first()
        
        if not customer:
            messages.error(request, "Aucun client trouvé. Veuillez créer un compte client.")
            return redirect('cmagic_sport:checkout')
        
        # Get cart items
        if not hasattr(cart, 'cart') or not cart.cart:
            messages.error(request, "Votre panier est vide.")
            return redirect('cmagic_sport:cart')
        
        cart_items = list(cart.cart.item_set.all())
        if not cart_items:
            messages.error(request, "Votre panier est vide.")
            return redirect('cmagic_sport:cart')
        
        # Calculate totals
        subtotal = sum(item.total_price for item in cart_items)
        tax = subtotal * 0.20
        total = subtotal + tax
        
        # Generate order number
        order_number = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Get form data - use getattr to safely access customer fields
        first_name = request.POST.get('first_name', getattr(customer, 'first_name', ''))
        last_name = request.POST.get('last_name', getattr(customer, 'last_name', ''))
        email = request.POST.get('email', getattr(customer, 'email', ''))
        phone = request.POST.get('phone', str(getattr(customer, 'phone_number', '') or ''))
        shipping_address = request.POST.get('address', getattr(customer, 'address1', ''))
        shipping_city = request.POST.get('city', '')
        shipping_postal_code = request.POST.get('zip_code', '')
        shipping_country = request.POST.get('country', 'France')
        
        # Create Order
        order = Order.objects.create(
            order_number=order_number,
            customer=customer,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            subtotal=subtotal,
            tax_amount=tax,
            total=total,
            status='pending',
        )
        
        # Create OrderItems
        for item in cart_items:
            # Calculate total price (since OrderItem uses a property)
            item_total = item.unit_price * item.quantity
            OrderItem.objects.create(
                order=order,
                product=item.product if hasattr(item, 'product') else None,
                product_name=item.product.name if hasattr(item, 'product') and item.product else 'Product',
                product_sku=item.product.sku if hasattr(item, 'product') and item.product else '',
                product_size=getattr(item, 'size', ''),
                product_color=getattr(item, 'color', ''),
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        
        # Clear the cart
        cart.clear()
        
        # Store order number in session for success page
        request.session['last_order_number'] = order_number
        request.session['last_order_id'] = order.id
        
        messages.success(request, f"Commande {order_number} créée avec succès!")
        return redirect('cmagic_sport:checkout_success')


class CheckoutSuccessView(TemplateView):
    """
    Vue confirmation de commande.
    
    URL: /cmagic-sport/checkout/success/
    """
    template_name = 'cmagic_sport/checkout_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get order from session
        order_id = self.request.session.get('last_order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                context['order'] = order
            except Order.DoesNotExist:
                context['order'] = {
                    'order_number': self.request.session.get('last_order_number', 'N/A'),
                }
        else:
            context['order'] = {
                'order_number': self.request.session.get('last_order_number', 'N/A'),
            }
        
        return context


# Import timezone for the success view
from django.utils import timezone

# ============================================
# Espace Client - Vues pour le suivi des commandes
# ============================================

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse

from .models import Order, OrderItem
from .serializers import OrderListSerializer, OrderDetailSerializer
from customer.models import Customer

User = get_user_model()


class CustomerSpaceMixin(LoginRequiredMixin):
    """
    Mixin pour l'espace client - verifie que l'utilisateur est connecte
    et recupere le client associe.
    """
    
    def get_customer(self):
        """Recupere le client associe a l'utilisateur connecte."""
        if hasattr(self.request.user, 'customer'):
            return self.request.user.customer
        # Fallback: chercher par email
        return Customer.objects.filter(
            Q(created_by__email=self.request.user.email) |
            Q(email=self.request.user.email)
        ).first()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_customer()
        context['customer'] = customer
        return context


class CustomerDashboardView(CustomerSpaceMixin, TemplateView):
    """
    Tableau de bord de l'espace client.
    
    Affiche un resume des commandes etaccès rapide aux fonctions.
    
    URL: /cmagic-sport/account/
    """
    template_name = 'cmagic_sport/customer/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_customer()
        
        if customer:
            # Recuperer les dernieres commandes
            recent_orders = Order.objects.filter(
                customer=customer
            ).order_by('-created_at')[:5]
            
            # Statistiques
            total_orders = Order.objects.filter(customer=customer).count()
            pending_orders = Order.objects.filter(
                customer=customer,
                status='pending'
            ).count()
            delivered_orders = Order.objects.filter(
                customer=customer,
                status='delivered'
            ).count()
            
            context['recent_orders'] = recent_orders
            context['total_orders'] = total_orders
            context['pending_orders'] = pending_orders
            context['delivered_orders'] = delivered_orders
        
        return context


class OrderListView(CustomerSpaceMixin, ListView):
    """
    Liste de toutes les commandes du client.
    
    URL: /cmagic-sport/account/orders/
    """
    model = Order
    template_name = 'cmagic_sport/customer/orders.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        customer = self.get_customer()
        if not customer:
            return Order.objects.none()
        return Order.objects.filter(
            customer=customer
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les filtres de statut
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class OrderDetailView(CustomerSpaceMixin, DetailView):
    """
    Detail d'une commande avec suivi.
    
    URL: /cmagic-sport/account/orders/<order_number>/
    """
    model = Order
    template_name = 'cmagic_sport/customer/order_detail.html'
    context_object_name = 'order'
    lookup_field = 'order_number'
    
    def get_object(self):
        customer = self.get_customer()
        order_number = self.kwargs.get('order_number')
        return get_object_or_404(
            Order,
            order_number=order_number,
            customer=customer
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        
        # Ajouter la progression du statut
        context['status_progress'] = order.get_status_progress()
        
        # Ajouter les items de la commande
        context['order_items'] = order.items.all()
        
        return context


class CustomerProfileView(CustomerSpaceMixin, UpdateView):
    """
    Modification du profil client.
    
    URL: /cmagic-sport/account/profile/
    """
    template_name = 'cmagic_sport/customer/profile.html'
    
    def get_object(self):
        return self.request.user
    
    def get_success_url(self):
        messages.success(self.request, 'Profil mis à jour avec succès!')
        return reverse('cmagic_sport:customer_profile')
    
    def get_form_class(self):
        from django import forms
        from customer.forms import UserChangeForm
        return UserChangeForm
    
    def form_valid(self, form):
        messages.success(self.request, 'Vos informations ont été mises à jour.')
        return super().form_valid(form)


# ============================================
# API Views pour l'Espace Client
# ============================================

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class CustomerOrderListAPIView(APIView):
    """
    API: Liste des commandes du client connecte.
    
    GET /api/v1/cmagic-sport/account/orders/
    """
    
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        customer = Customer.objects.filter(
            Q(user__email=request.user.email) |
            Q(email=request.user.email)
        ).first()
        
        if not customer:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        
        # Filtre par statut
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


class CustomerOrderDetailAPIView(APIView):
    """
    API: Detail d'une commande.
    
    GET /api/v1/cmagic-sport/account/orders/<order_number>/
    """
    
    def get(self, request, order_number):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        customer = Customer.objects.filter(
            Q(user__email=request.user.email) |
            Q(email=request.user.email)
        ).first()
        
        if not customer:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order = Order.objects.filter(
            order_number=order_number,
            customer=customer
        ).first()
        
        if not order:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)


class OrderTrackingAPIView(APIView):
    """
    API: Suivi d'une commande par numero.
    
    GET /api/v1/cmagic-sport/track/<order_number>/
    """
    
    def get(self, request, order_number):
        order = Order.objects.filter(
            order_number=order_number
        ).first()
        
        if not order:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)