"""ecommerce URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

app_name = 'config'

urlpatterns = [
    # contrib, admin
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # API Documentation - Swagger/OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # Unified API v1
    path('api/v1/', include('config.api_urls')),
    # apps local
    path('', include('product.urls'), name='home'),
    path('proj/', include('project.urls'), name='proj_home'),
    path('shop/', include('shop.urls'), name='sh_home'),
    path('cart/', include('core.cart.urls')),
    path("customer/", include("customer.urls")),
    # invoices
    path("invoice/", include('invoice.urls')),
    path('devis/', include('devis.urls')),  # Devis
    path('mfu/', include("core.mfilesupload.urls")),
    # Order:la commande
    path("order/", include('core.orders.urls')),
    # Streams & Milestones API (legacy path, kept for backward compatibility)
    path("api/streams/", include("core.streams.urls")),
    ## Projet Immobilier
    #path('', include('immoshop.urls', 'immoshop')),
    ## Projet Concession Auto
    #path('carshop/', include(('autocar.urls', 'carshop'), namespace='carshop')),
]
# ... the rest of your URLconf goes here ...
## add static
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
## add static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# add debug_toolbar
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += path('__debug__', include(debug_toolbar.urls)),
