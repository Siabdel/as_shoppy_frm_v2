"""
API Documentation Tests

Tests for Swagger/OpenAPI documentation endpoints.
"""
import pytest
from rest_framework import status


@pytest.mark.django_db
class TestAPIDocumentation:
    """Test suite for API documentation endpoints."""
    
    def test_swagger_ui_accessible(self, authenticated_client):
        """Test that Swagger UI is accessible."""
        url = '/api/docs/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert b'Swagger' in response.content or b'swagger' in response.content
    
    def test_redoc_accessible(self, authenticated_client):
        """Test that ReDoc is accessible."""
        url = '/api/redoc/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert b'ReDoc' in response.content or b'redoc' in response.content.lower()
    
    def test_openapi_schema_accessible(self, authenticated_client):
        """Test that OpenAPI schema is accessible."""
        url = '/api/schema/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'openapi' in response.data
        assert 'paths' in response.data
    
    def test_openapi_schema_contains_endpoints(self, authenticated_client):
        """Test that OpenAPI schema contains API endpoints."""
        url = '/api/schema/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        paths = response.data.get('paths', {})
        
        # Check for main API endpoints
        assert any('streams' in path for path in paths.keys())
        assert any('milestones' in path for path in paths.keys())
        assert any('products' in path for path in paths.keys())
        assert any('customers' in path for path in paths.keys())
        assert any('projects' in path for path in paths.keys())
    
    def test_openapi_schema_version(self, authenticated_client):
        """Test that OpenAPI schema has correct version."""
        url = '/api/schema/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('info', {}).get('version') == '1.0.0'
        assert response.data.get('info', {}).get('title') == 'AS-Shopy API'
