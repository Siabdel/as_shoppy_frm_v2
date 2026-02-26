from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Q
from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from immoshopy import models as im_models
from django.shortcuts import render
from product.models import Product
from project.models import Project
# Create your views here.


def search(request):
    query = request.GET.get('q')
    if query:
        projects = Project.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
        products = Product.objects.filter(
            Q(product_name__icontains=query) | Q(project__name__icontains=query)
        )
    else:
        projects = Project.objects.none()
        products = Product.objects.none()

    context = {
        'projects': projects,
        'products': products,
        'query': query,
    }
    return render(request, 'immoshopy/search_results.html', context)
class HomeView(ListView):
    template_name="immoshopy/home_page.html"
    model = im_models.ImmoProduct
    context_object_name = "products"
    
    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset()
    
def home_page(request):
    context = {
        'featured_projects': Project.objects.all(),
        'recent_products': Product.objects.order_by('-created_at')[:4],
        'all_projects': Project.objects.all(),
    }
    return render(request, 'immoshopy/home_page.html', context)

class ImmoDetailView(DetailView):
    pass

