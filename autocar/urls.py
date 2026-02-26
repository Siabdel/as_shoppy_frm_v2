from django.urls import path
from django.urls import reverse, reverse_lazy
from weasyprint import HTML
from shop import views as shop_models 

app_name = 'carshop'  # Ceci définit l'espace de noms pour l'application

urlpatterns = [
    path('show/<int:pk>/', shop_models.ProductDetailView.as_view(), name='product_car_detail'),
]