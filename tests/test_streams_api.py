"""
Streams API Tests

Comprehensive tests for the Streams and Milestones API endpoints.
"""
import pytest
from django.urls import reverse
from rest_framework import status

from core.streams.models import Stream, StreamEvent, Milestone, StreamSubscription
from core.streams.enums import StreamType, EventType, MilestoneStatus, SubscriptionType


@pytest.mark.django_db
class TestStreamAPI:
    """Test suite for Stream API endpoints."""
    
    def test_list_streams(self, authenticated_client, api_url, stream):
        """Test listing all streams."""
        url = f"{api_url}streams/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['name'] == stream.name
    
    def test_create_stream(self, authenticated_client, api_url, user):
        """Test creating a new stream."""
        url = f"{api_url}streams/"
        data = {
            'name': 'New Test Stream',
            'description': 'A new test stream',
            'stream_type': 'project',
            'is_active': True,
            'is_public': True
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Test Stream'
        assert response.data['slug'] == 'new-test-stream'
    
    def test_retrieve_stream(self, authenticated_client, api_url, stream):
        """Test retrieving a specific stream."""
        url = f"{api_url}streams/{stream.slug}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == stream.name
        assert response.data['slug'] == stream.slug
    
    def test_update_stream(self, authenticated_client, api_url, stream):
        """Test updating a stream."""
        url = f"{api_url}streams/{stream.slug}/"
        data = {
            'name': 'Updated Stream Name',
            'description': 'Updated description'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Stream Name'
    
    def test_delete_stream(self, authenticated_client, api_url, stream):
        """Test deleting a stream."""
        url = f"{api_url}streams/{stream.slug}/"
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Stream.objects.filter(slug=stream.slug).exists()
    
    def test_stream_filter_by_type(self, authenticated_client, api_url, stream):
        """Test filtering streams by type."""
        url = f"{api_url}streams/?type=project"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for result in response.data['results']:
            assert result['stream_type'] == 'project'
    
    def test_stream_search(self, authenticated_client, api_url, stream):
        """Test searching streams."""
        url = f"{api_url}streams/?search={stream.name}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_add_event_to_stream(self, authenticated_client, api_url, stream):
        """Test adding an event to a stream."""
        url = f"{api_url}streams/{stream.slug}/add_event/"
        data = {
            'event_type': 'project_created',
            'description': 'Test event from API',
            'importance': 'high'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['description'] == 'Test event from API'
    
    def test_get_stream_events(self, authenticated_client, api_url, stream, stream_event):
        """Test getting events for a stream."""
        url = f"{api_url}streams/{stream.slug}/events/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_subscribe_to_stream(self, authenticated_client, api_url, stream):
        """Test subscribing to a stream."""
        url = f"{api_url}streams/{stream.slug}/subscribe/"
        data = {'subscription_type': 'follow'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subscription_type'] == 'follow'
    
    def test_unauthenticated_access(self, api_client, api_url):
        """Test that unauthenticated requests are rejected."""
        url = f"{api_url}streams/"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestStreamEventAPI:
    """Test suite for StreamEvent API endpoints."""
    
    def test_list_events(self, authenticated_client, api_url, stream_event):
        """Test listing all stream events."""
        url = f"{api_url}stream-events/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_filter_events_by_stream(self, authenticated_client, api_url, stream, stream_event):
        """Test filtering events by stream."""
        url = f"{api_url}stream-events/?stream={stream.id}"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        for result in response.data['results']:
            assert result['stream'] == stream.id
    
    def test_filter_events_by_type(self, authenticated_client, api_url, stream_event):
        """Test filtering events by type."""
        url = f"{api_url}stream-events/?event_type=project_created"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMilestoneAPI:
    """Test suite for Milestone API endpoints."""
    
    def test_list_milestones(self, authenticated_client, api_url, milestone):
        """Test listing all milestones."""
        url = f"{api_url}milestones/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_milestone(self, authenticated_client, api_url, project):
        """Test creating a new milestone."""
        url = f"{api_url}milestones/"
        data = {
            'name': 'New Test Milestone',
            'description': 'A new test milestone',
            'project': project.id,
            'status': 'pending',
            'priority': 'high'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Test Milestone'
    
    def test_retrieve_milestone(self, authenticated_client, api_url, milestone):
        """Test retrieving a specific milestone."""
        url = f"{api_url}milestones/{milestone.slug}/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == milestone.name
    
    def test_update_milestone(self, authenticated_client, api_url, milestone):
        """Test updating a milestone."""
        url = f"{api_url}milestones/{milestone.slug}/"
        data = {'progress_percentage': 50}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_update_progress(self, authenticated_client, api_url, milestone):
        """Test updating milestone progress."""
        url = f"{api_url}milestones/{milestone.slug}/update_progress/"
        data = {'progress_percentage': 75}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['progress_percentage'] == 75
    
    def test_add_comment(self, authenticated_client, api_url, milestone):
        """Test adding a comment to a milestone."""
        url = f"{api_url}milestones/{milestone.slug}/add_comment/"
        data = {'content': 'This is a test comment'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'This is a test comment'
    
    def test_filter_milestones_by_status(self, authenticated_client, api_url, milestone):
        """Test filtering milestones by status."""
        url = f"{api_url}milestones/?status=pending"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestStreamSubscriptionAPI:
    """Test suite for StreamSubscription API endpoints."""
    
    def test_list_subscriptions(self, authenticated_client, api_url, user, stream):
        """Test listing user's subscriptions."""
        # Create a subscription first
        StreamSubscription.objects.create(
            user=user,
            stream=stream,
            subscription_type=SubscriptionType.FOLLOW
        )
        
        url = f"{api_url}subscriptions/"
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_create_subscription(self, authenticated_client, api_url, stream):
        """Test creating a new subscription."""
        url = f"{api_url}subscriptions/"
        data = {
            'stream': stream.id,
            'subscription_type': 'watch'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subscription_type'] == 'watch'
