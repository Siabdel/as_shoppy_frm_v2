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
    
    # ========================================
    # Espace Client - Suivi de commandes
    # ========================================
    path(
        'account/',
        views.CustomerDashboardView.as_view(),
        name='customer_dashboard'
    ),
    path(
        'account/orders/',
        views.OrderListView.as_view(),
        name='customer_orders'
    ),
    path(
        'account/orders/<str:order_number>/',
        views.OrderDetailView.as_view(),
        name='order_detail'
    ),
    path(
        'account/profile/',
        views.CustomerProfileView.as_view(),
        name='customer_profile'
    ),
    
    # API: Suivi de commande public (par numero)
    path(
        'api/v1/track/<str:order_number>/',
        views.OrderTrackingAPIView.as_view(),
        name='order_tracking_api'
    ),
    
    # API: Espace Client
    path(
        'api/v1/account/orders/',
        views.CustomerOrderListAPIView.as_view(),
        name='customer_orders_api'
    ),
    path(
        'api/v1/account/orders/<str:order_number>/',
        views.CustomerOrderDetailAPIView.as_view(),
        name='customer_order_detail_api'
    ),
]