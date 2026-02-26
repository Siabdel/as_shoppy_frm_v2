"""
ImmoProducts API Tests

Comprehensive tests for the ImmoProducts (Real Estate) API endpoints.
"""
import pytest
from rest_framework import status

from immoshopy.models import ImmoProduct


@pytest.mark.django_db
class TestImmoProductAPI:
    """Test suite for ImmoProduct API endpoints."""
    
    def test_list_immoproducts(self, authenticated_client, api_url, immo_product):
        """Test listing all immo products."""
        url = f"{api_url}immoproducts/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_immoproduct(self, authenticated_client, api_url, project):
        """Test creating a new immo product."""
        url = f"{api_url}immoproducts/"
        data = {
            'project': project.id,
            'name': 'New Test Property',
            'description': 'A beautiful test property',
            'price': 350000.00,
            'stock': 1,
            'available': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Test Property'
    
    def test_retrieve_immoproduct(self, authenticated_client, api_url, immo_product):
        """Test retrieving a specific immo product."""
        url = f"{api_url}immoproducts/{immo_product.slug}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == immo_product.name
    
    def test_update_immoproduct(self, authenticated_client, api_url, immo_product):
        """Test updating an immo product."""
        url = f"{api_url}immoproducts/{immo_product.slug}/"
        data = {'price': 275000.00}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_delete_immoproduct(self, authenticated_client, api_url, immo_product):
        """Test deleting an immo product."""
        url = f"{api_url}immoproducts/{immo_product.slug}/"
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ImmoProduct.objects.filter(slug=immo_product.slug).exists()
    
    def test_filter_immoproducts_by_availability(self, authenticated_client, api_url, immo_product):
        """Test filtering immo products by availability."""
        url = f"{api_url}immoproducts/?available=true"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for result in response.data['results']:
            assert result['available'] is True
    
    def test_filter_immoproducts_by_price_range(self, authenticated_client, api_url, immo_product):
        """Test filtering immo products by price range."""
        url = f"{api_url}immoproducts/?min_price=100000&max_price=500000"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_toggle_availability(self, authenticated_client, api_url, immo_product):
        """Test toggling immo product availability."""
        original_status = immo_product.available
        url = f"{api_url}immoproducts/{immo_product.slug}/toggle_availability/"
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['available'] is not original_status
    
    def test_update_stock(self, authenticated_client, api_url, immo_product):
        """Test updating immo product stock."""
        url = f"{api_url}immoproducts/{immo_product.slug}/update_stock/"
        data = {'stock': 5}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['stock'] == 5
    
    def test_get_immoproduct_images(self, authenticated_client, api_url, immo_product):
        """Test getting immo product images."""
        url = f"{api_url}immoproducts/{immo_product.slug}/images/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_immoproduct_stats(self, authenticated_client, api_url, immo_product):
        """Test getting immo product statistics."""
        url = f"{api_url}immoproducts/stats/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_products' in response.data
        assert 'price_statistics' in response.data
    
    def test_unauthenticated_access(self, api_client, api_url):
        """Test that unauthenticated requests are rejected."""
        url = f"{api_url}immoproducts/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
