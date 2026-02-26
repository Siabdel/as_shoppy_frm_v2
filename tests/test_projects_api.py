"""
Projects API Tests

Comprehensive tests for the Projects API endpoints.
"""
import pytest
from rest_framework import status

from project.models import Project


@pytest.mark.django_db
class TestProjectAPI:
    """Test suite for Project API endpoints."""
    
    def test_list_projects(self, authenticated_client, api_url, project):
        """Test listing all projects."""
        url = f"{api_url}projects/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_project(self, authenticated_client, api_url):
        """Test creating a new project."""
        url = f"{api_url}projects/"
        data = {
            'name': 'New Test Project',
            'description': 'A new test project',
            'status': 'active'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Test Project'
    
    def test_retrieve_project(self, authenticated_client, api_url, project):
        """Test retrieving a specific project."""
        url = f"{api_url}projects/{project.slug}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == project.name
    
    def test_update_project(self, authenticated_client, api_url, project):
        """Test updating a project."""
        url = f"{api_url}projects/{project.slug}/"
        data = {'description': 'Updated description'}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated description'
    
    def test_delete_project(self, authenticated_client, api_url, project):
        """Test deleting a project."""
        url = f"{api_url}projects/{project.slug}/"
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Project.objects.filter(slug=project.slug).exists()
    
    def test_get_project_milestones(self, authenticated_client, api_url, project, milestone):
        """Test getting project milestones."""
        url = f"{api_url}projects/{project.slug}/milestones/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'milestone_count' in response.data
    
    def test_get_project_products(self, authenticated_client, api_url, project, product):
        """Test getting project products."""
        url = f"{api_url}projects/{project.slug}/products/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'product_count' in response.data
    
    def test_get_project_stream(self, authenticated_client, api_url, project, stream):
        """Test getting project activity stream."""
        # Associate stream with project
        stream.content_object = project
        stream.save()
        
        url = f"{api_url}projects/{project.slug}/stream/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_get_project_stats(self, authenticated_client, api_url, project):
        """Test getting project statistics."""
        url = f"{api_url}projects/stats/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_projects' in response.data
        assert 'active' in response.data
    
    def test_archive_project(self, authenticated_client, api_url, project):
        """Test archiving a project."""
        url = f"{api_url}projects/{project.slug}/archive/"
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'project archived'
    
    def test_filter_projects_by_status(self, authenticated_client, api_url, project):
        """Test filtering projects by status."""
        url = f"{api_url}projects/?status=active"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_search_projects(self, authenticated_client, api_url, project):
        """Test searching projects."""
        url = f"{api_url}projects/?search={project.name}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_unauthenticated_access(self, api_client, api_url):
        """Test that unauthenticated requests are rejected."""
        url = f"{api_url}projects/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
