"""
Products API Tests

Comprehensive tests for the Products API endpoints.
"""
import pytest
from rest_framework import status

from product.models import Product


@pytest.mark.django_db
class TestProductAPI:
    """Test suite for Product API endpoints."""
    
    def test_list_products(self, authenticated_client, api_url, product):
        """Test listing all products."""
        url = f"{api_url}products/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_product(self, authenticated_client, api_url, project):
        """Test creating a new product."""
        url = f"{api_url}products/"
        data = {
            'project': project.id,
            'name': 'New Test Product',
            'description': 'A new test product',
            'price': 149.99,
            'stock': 20,
            'available': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Test Product'
    
    def test_retrieve_product(self, authenticated_client, api_url, product):
        """Test retrieving a specific product."""
        url = f"{api_url}products/{product.slug}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == product.name
    
    def test_update_product(self, authenticated_client, api_url, product):
        """Test updating a product."""
        url = f"{api_url}products/{product.slug}/"
        data = {'price': 199.99, 'stock': 15}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['price'] == '199.99'
    
    def test_delete_product(self, authenticated_client, api_url, product):
        """Test deleting a product."""
        url = f"{api_url}products/{product.slug}/"
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Product.objects.filter(slug=product.slug).exists()
    
    def test_filter_products_by_availability(self, authenticated_client, api_url, product):
        """Test filtering products by availability."""
        url = f"{api_url}products/?available=true"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for result in response.data['results']:
            assert result['available'] is True
    
    def test_filter_products_by_price_range(self, authenticated_client, api_url, product):
        """Test filtering products by price range."""
        url = f"{api_url}products/?min_price=50&max_price=150"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_products(self, authenticated_client, api_url, product):
        """Test searching products."""
        url = f"{api_url}products/?search={product.name}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_toggle_availability(self, authenticated_client, api_url, product):
        """Test toggling product availability."""
        original_status = product.available
        url = f"{api_url}products/{product.slug}/toggle_availability/"
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['available'] is not original_status
    
    def test_update_stock(self, authenticated_client, api_url, product):
        """Test updating product stock."""
        url = f"{api_url}products/{product.slug}/update_stock/"
        data = {'stock': 50}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['stock'] == 50
    
    def test_get_product_images(self, authenticated_client, api_url, product):
        """Test getting product images."""
        url = f"{api_url}products/{product.slug}/images/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_access(self, api_client, api_url):
        """Test that unauthenticated requests are rejected."""
        url = f"{api_url}products/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
