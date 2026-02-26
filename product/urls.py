
from django.urls import path, include
from .api_views import ProductViewSet
from .routers import router

app_name="product"


urlpatterns = [
    #path('', ListView.as_view(), name='product_list'),
    path('', include(router.urls)),
    path('api/', include(router.urls)),
]