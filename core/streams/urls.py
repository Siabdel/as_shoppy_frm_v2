"""
Stream & Milestone URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'streams', views.StreamViewSet, basename='stream')
router.register(r'milestones', views.MilestoneViewSet, basename='milestone')
router.register(r'subscriptions', views.StreamSubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]