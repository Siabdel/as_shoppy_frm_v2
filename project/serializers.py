"""
Project Serializers

Django REST Framework serializers for the project API.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Project, Task, Ticket


class UserSerializer(serializers.ModelSerializer):
    """Simplified User serializer for nesting."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    
    Provides full project details including related objects.
    """
    author = UserSerializer(read_only=True)
    manager = UserSerializer(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    task_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'slug', 'description',
            'status', 'status_display',
            'start_date', 'end_date', 'due_date', 'closed_date',
            'author', 'manager', 
            'societe', 'category',
            'lon', 'lat', 'active',
            'created_at', 'updated_at',
            'task_count', 'ticket_count', 'product_count', 'image_count',
            'default_image', 'visibilite', 'comment'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at', 'code']
    
    def get_task_count(self, obj):
        """Return the number of tasks for this project."""
        return obj.tasks.count()
    
    def get_ticket_count(self, obj):
        """Return the number of tickets for this project."""
        return obj.tickets.count()
    
    def get_product_count(self, obj):
        """Return the number of products for this project."""
        return obj.product_set.count()
    
    def get_image_count(self, obj):
        """Return the number of images for this project."""
        return obj.images.count()
    
    def create(self, validated_data):
        """Create a new project."""
        return Project.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing project."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for project list views.
    
    Provides essential information for list displays.
    """
    author_username = serializers.CharField(
        source='author.username', read_only=True
    )
    manager_username = serializers.CharField(
        source='manager.username', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'slug', 
            'author_username', 'manager_username',
            'status', 'status_display',
            'start_date', 'end_date', 
            'item_count', 'created_at', 'active'
        ]
    
    def get_item_count(self, obj):
        """Return total items (tasks + tickets + products) count."""
        return obj.tasks.count() + obj.tickets.count() + obj.product_set.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new projects.
    """
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description',
            'status', 'start_date', 'end_date', 'due_date',
            'societe', 'category', 'lon', 'lat'
        ]
        read_only_fields = ['id']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.
    """
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_slug = serializers.CharField(source='project.slug', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'project', 'project_name', 'project_slug',
            'created_by', 'assigned_to',
            'status', 'priority', 'task_type',
            'created_at', 'updated_at', 'completed_at', 'due_date'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating tasks.
    """
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description',
            'project', 'assigned_to',
            'status', 'priority', 'task_type',
            'due_date'
        ]


class TicketSerializer(serializers.ModelSerializer):
    """
    Serializer for Ticket model.
    """
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_slug = serializers.CharField(source='project.slug', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'resolution',
            'project', 'project_name', 'project_slug',
            'created_by', 'assigned_to',
            'status', 'priority', 'ticket_type',
            'created_at', 'updated_at', 'resolved_at', 'due_date'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TicketCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating tickets.
    """
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'resolution',
            'project', 'assigned_to',
            'status', 'priority', 'ticket_type',
            'due_date'
        ]
