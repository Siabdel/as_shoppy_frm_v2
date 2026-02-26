from rest_framework.routers import DefaultRouter
from .api_views import (
    ProductViewSet, ProductImageViewSet,
    ProductTypeViewSet, ProductSpecificationViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'product-types', ProductTypeViewSet, basename='product-type')
router.register(r'product-specifications', ProductSpecificationViewSet, basename='product-specification')
