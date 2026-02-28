from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from product.models import Product
from core.taxonomy.models import MPCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


class ProductListView(ListView):
    """
    Product list view with filtering and pagination
    """
    model = Product
    template_name = 'product/home.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Filter by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MPCategory.objects.filter(is_active=True)
        return context


class ProductShopListView(ListView):
    """
    Shop product list view with CMagic template
    """
    model = Product
    template_name = 'product/product_list_cmagic.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        # Filter by category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = MPCategory.objects.filter(is_active=True)
        return context


class ProductDetailView(DetailView):
    """
    Product detail view
    """
    model = Product
    template_name = 'product/product_detail_cmagic.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related products from same category
        if self.object.category:
            context['related_products'] = Product.objects.filter(
                category=self.object.category,
                is_active=True
            ).exclude(pk=self.object.pk)[:4]
        return context


def product_list(request):
    """
    Simple product list view
    """
    products = Product.objects.filter(is_active=True)[:12]
    categories = MPCategory.objects.filter(is_active=True)
    
    return render(request, 'product/home.html', {
        'products': products,
        'categories': categories
    })


def product_shop_detail(request, pk):
    """
    Product detail view for shop
    """
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Get related products
    related_products = []
    if product.category:
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(pk=pk)[:4]
    
    return render(request, 'product/product_detail_cmagic.html', {
        'product': product,
        'related_products': related_products
    })
