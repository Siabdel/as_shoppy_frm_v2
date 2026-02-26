"""
Pytest Configuration and Fixtures

This module provides shared fixtures for all API tests.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.streams.models import Stream, StreamEvent, Milestone
from core.streams.enums import StreamType, EventType, MilestoneStatus
from customer.models import Customer
from project.models import Project
from product.models import Product
from immoshopy.models import ImmoProduct


@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user(db):
    """Create and return a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def user_token(user):
    """Create and return an auth token for the test user."""
    return Token.objects.create(user=user)


@pytest.fixture
def project(db, user):
    """Create and return a test project."""
    return Project.objects.create(
        name='Test Project',
        description='A test project for API testing',
        created_by=user,
        status='active'
    )


@pytest.fixture
def stream(db, user):
    """Create and return a test stream."""
    return Stream.objects.create(
        name='Test Stream',
        description='A test stream for API testing',
        stream_type=StreamType.PROJECT,
        created_by=user,
        is_active=True,
        is_public=True
    )


@pytest.fixture
def stream_event(db, stream, user):
    """Create and return a test stream event."""
    return StreamEvent.objects.create(
        stream=stream,
        event_type=EventType.PROJECT_CREATED,
        description='Test event created during API testing',
        actor=user,
        importance='normal'
    )


@pytest.fixture
def milestone(db, project, user):
    """Create and return a test milestone."""
    return Milestone.objects.create(
        name='Test Milestone',
        description='A test milestone for API testing',
        project=project,
        created_by=user,
        status=MilestoneStatus.PENDING,
        priority='medium'
    )


@pytest.fixture
def customer(db, user):
    """Create and return a test customer."""
    return Customer.objects.create(
        user=user,
        state=2,  # REGISTERED
        recognized=True
    )


@pytest.fixture
def product(db, project):
    """Create and return a test product."""
    return Product.objects.create(
        project=project,
        name='Test Product',
        description='A test product for API testing',
        price=99.99,
        stock=10,
        available=True
    )


@pytest.fixture
def immo_product(db, project):
    """Create and return a test immo product."""
    return ImmoProduct.objects.create(
        project=project,
        name='Test Immo Product',
        description='A test real estate product',
        price=250000.00,
        stock=1,
        available=True
    )


@pytest.fixture
def api_url():
    """Return the base API URL."""
    return '/api/v1/'
