"""
Unified API URL Configuration

This module provides a centralized API routing for all apps.
All API endpoints are prefixed with /api/v1/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets from each app
from core.streams.views import (
    StreamViewSet,
    StreamEventViewSet,
    MilestoneViewSet,
    StreamSubscriptionViewSet,
    MilestoneCommentViewSet
)
from product.api_views import (
    ProductViewSet, ProductImageViewSet,
    ProductTypeViewSet, ProductSpecificationViewSet
)
from customer.api_views import CustomerViewSet
from immoshopy.api_views import ImmoProductViewSet
from project.api_views import ProjectViewSet, TaskViewSet, TicketViewSet
from devis.api_views import QuoteViewSet, QuoteItemViewSet

# Create a router and register viewsets
router = DefaultRouter()

# Streams & Milestones
router.register(r'streams', StreamViewSet, basename='stream')
router.register(r'stream-events', StreamEventViewSet, basename='stream-event')
router.register(r'milestones', MilestoneViewSet, basename='milestone')
router.register(r'subscriptions', StreamSubscriptionViewSet, basename='subscription')
router.register(r'milestone-comments', MilestoneCommentViewSet, basename='milestone-comment')

# Products
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'product-types', ProductTypeViewSet, basename='product-type')
router.register(r'product-specifications', ProductSpecificationViewSet, basename='product-specification')

# Customers
router.register(r'customers', CustomerViewSet, basename='customer')

# Immobilier
router.register(r'immoproducts', ImmoProductViewSet, basename='immoproduct')

# Projects
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'tickets', TicketViewSet, basename='ticket')

# Quotes (Devis)
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-items', QuoteItemViewSet, basename='quote-item')

urlpatterns = [
    path('', include(router.urls)),
]
