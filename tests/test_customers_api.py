"""
Customers API Tests

Comprehensive tests for the Customers API endpoints.
"""
import pytest
from rest_framework import status

from customer.models import Customer


@pytest.mark.django_db
class TestCustomerAPI:
    """Test suite for Customer API endpoints."""
    
    def test_list_customers(self, authenticated_client, api_url, customer):
        """Test listing all customers."""
        url = f"{api_url}customers/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_retrieve_customer(self, authenticated_client, api_url, customer):
        """Test retrieving a specific customer."""
        url = f"{api_url}customers/{customer.id}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == customer.id
    
    def test_update_customer(self, authenticated_client, api_url, customer):
        """Test updating a customer."""
        url = f"{api_url}customers/{customer.id}/"
        data = {'state': 1}  # Set as guest
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_recognize_customer(self, authenticated_client, api_url, customer):
        """Test recognizing a customer."""
        customer.recognized = False
        customer.save()
        
        url = f"{api_url}customers/{customer.id}/recognize/"
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['recognized'] is True
    
    def test_set_guest(self, authenticated_client, api_url, customer):
        """Test setting customer as guest."""
        url = f"{api_url}customers/{customer.id}/set_guest/"
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['state'] == 1  # GUEST
    
    def test_get_customer_orders(self, authenticated_client, api_url, customer):
        """Test getting customer orders."""
        url = f"{api_url}customers/{customer.id}/orders/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'order_count' in response.data
    
    def test_get_customer_stats(self, authenticated_client, api_url, customer):
        """Test getting customer statistics."""
        url = f"{api_url}customers/stats/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_customers' in response.data
        assert 'recognized' in response.data
    
    def test_filter_customers_by_state(self, authenticated_client, api_url, customer):
        """Test filtering customers by state."""
        url = f"{api_url}customers/?state=2"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_customers(self, authenticated_client, api_url, customer):
        """Test searching customers."""
        url = f"{api_url}customers/?search={customer.user.username}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_access(self, api_client, api_url):
        """Test that unauthenticated requests are rejected."""
        url = f"{api_url}customers/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
