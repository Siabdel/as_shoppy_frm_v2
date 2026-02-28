from django.urls import path, include
from .api_views import ProductViewSet
from .routers import router
from . import views

app_name = "product"


urlpatterns = [
    # Home/Shop product list
    path('', views.product_list, name='product_list'),
    path('shop/', views.ProductShopListView.as_view(), name='shop_product_list'),
    path('product/<int:pk>/', views.product_shop_detail, name='product_shop_detail'),
    
    # API routes
    path('api/', include(router.urls)),
]
