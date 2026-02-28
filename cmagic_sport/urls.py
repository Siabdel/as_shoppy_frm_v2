# -*- coding: utf-8 -*-
"""
URLs pour CMagic Sport.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Router pour les endpoints API REST
router = DefaultRouter()
router.register(
    r'products',
    views.SportProductViewSet,
    basename='sport-product'
)

app_name = 'cmagic_sport'

urlpatterns = [
    # Endpoints API REST
    path('api/v1/', include(router.urls)),
    
    # URLs publiques - Vitrine Client
    path(
        '',
        views.CatalogView.as_view(),
        name='catalog'
    ),
    path(
        'product/<slug:slug>/',
        views.ProductDetailView.as_view(),
        name='product_detail'
    ),
    path(
        'cart/',
        views.CartView.as_view(),
        name='cart'
    ),
    path(
        'checkout/',
        views.CheckoutView.as_view(),
        name='checkout'
    ),
    path(
        'checkout/success/',
        views.CheckoutSuccessView.as_view(),
        name='checkout_success'
    ),
]