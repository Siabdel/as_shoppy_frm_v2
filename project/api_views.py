"""
Project API Views

REST API endpoints for project management.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Project, Task, Ticket
from .serializers import (
    ProjectSerializer, ProjectListSerializer, 
    TaskSerializer, TicketSerializer
)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects.
    
    Provides CRUD operations and additional actions for project management.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'slug', 'code']
    ordering_fields = ['created_at', 'updated_at', 'name', 'start_date']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        """Filter projects based on user permissions and query params."""
        queryset = Project.objects.all()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by author
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author__username=author)
        
        # Filter by manager
        manager = self.request.query_params.get('manager')
        if manager:
            queryset = queryset.filter(manager__username=manager)
        
        # Filter by date range
        start_after = self.request.query_params.get('start_after')
        start_before = self.request.query_params.get('start_before')
        if start_after:
            queryset = queryset.filter(start_date__gte=start_after)
        if start_before:
            queryset = queryset.filter(start_date__lte=start_before)
        
        return queryset.select_related('author', 'manager', 'societe')
    
    def perform_create(self, serializer):
        """Set the author field to current user."""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, slug=None):
        """Get all tasks for a project."""
        project = self.get_object()
        tasks = project.tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response({
            'project_slug': project.slug,
            'project_name': project.name,
            'task_count': tasks.count(),
            'tasks': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def tickets(self, request, slug=None):
        """Get all tickets for a project."""
        project = self.get_object()
        tickets = project.tickets.all()
        serializer = TicketSerializer(tickets, many=True)
        return Response({
            'project_slug': project.slug,
            'project_name': project.name,
            'ticket_count': tickets.count(),
            'tickets': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get all products for a project."""
        project = self.get_object()
        products = project.product_set.all()
        return Response({
            'project_slug': project.slug,
            'project_name': project.name,
            'product_count': products.count(),
            'products': [
                {
                    'id': p.id,
                    'name': p.name or p.product_name,
                    'slug': p.slug,
                    'price': str(p.price),
                    'available': p.available
                }
                for p in products
            ]
        })
    
    @action(detail=True, methods=['get'])
    def images(self, request, slug=None):
        """Get all images for a project."""
        project = self.get_object()
        images = project.images.all()
        return Response({
            'project_slug': project.slug,
            'project_name': project.name,
            'image_count': images.count(),
            'images': [
                {
                    'id': img.id,
                    'title': img.title,
                    'image': request.build_absolute_uri(img.image.url) if img.image else None,
                    'thumbnail_path': img.thumbnail_path,
                    'large_path': img.large_path,
                }
                for img in images
            ]
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get project statistics."""
        from django.db.models import Count
        from .models import ProjectStatus
        
        total = Project.objects.count()
        planning = Project.objects.filter(status=ProjectStatus.PLANNING.code).count()
        under_construction = Project.objects.filter(status=ProjectStatus.UNDER_CONSTRUCTION.code).count()
        completed = Project.objects.filter(status=ProjectStatus.COMPLETED.code).count()
        selling = Project.objects.filter(status=ProjectStatus.SELLING.code).count()
        sold_out = Project.objects.filter(status=ProjectStatus.SOLD_OUT.code).count()
        
        # Projects with tasks
        with_tasks = Project.objects.annotate(
            task_count=Count('tasks')
        ).filter(task_count__gt=0).count()
        
        # Projects with tickets
        with_tickets = Project.objects.annotate(
            ticket_count=Count('tickets')
        ).filter(ticket_count__gt=0).count()
        
        # Projects with products
        with_products = Project.objects.annotate(
            product_count=Count('product')
        ).filter(product_count__gt=0).count()
        
        return Response({
            'total_projects': total,
            'planning': planning,
            'under_construction': under_construction,
            'completed': completed,
            'selling': selling,
            'sold_out': sold_out,
            'other_status': total - planning - under_construction - completed - selling - sold_out,
            'with_tasks': with_tasks,
            'with_tickets': with_tickets,
            'with_products': with_products
        })
    
    @action(detail=True, methods=['post'])
    def archive(self, request, slug=None):
        """Archive a project by setting status to CANCELLED."""
        project = self.get_object()
        from .models import ProjectStatus
        project.status = ProjectStatus.CANCELLED.code
        project.save()
        return Response(
            {'status': 'project archived', 'slug': project.slug, 'new_status': project.status},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, slug=None):
        """Activate a project by setting status to SELLING."""
        project = self.get_object()
        from .models import ProjectStatus
        project.status = ProjectStatus.SELLING.code
        project.save()
        return Response(
            {'status': 'project activated', 'slug': project.slug, 'new_status': project.status},
            status=status.HTTP_200_OK
        )


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    
    def get_queryset(self):
        """Filter tasks based on query params."""
        queryset = Task.objects.all()
        
        # Filter by project
        project_slug = self.request.query_params.get('project')
        if project_slug:
            queryset = queryset.filter(project__slug=project_slug)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to__username=assigned_to)
        
        return queryset.select_related('project', 'created_by', 'assigned_to')
    
    def perform_create(self, serializer):
        """Set the created_by field to current user."""
        serializer.save(created_by=self.request.user)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tickets.
    """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'resolution']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    
    def get_queryset(self):
        """Filter tickets based on query params."""
        queryset = Ticket.objects.all()
        
        # Filter by project
        project_slug = self.request.query_params.get('project')
        if project_slug:
            queryset = queryset.filter(project__slug=project_slug)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to__username=assigned_to)
        
        return queryset.select_related('project', 'created_by', 'assigned_to')
    
    def perform_create(self, serializer):
        """Set the created_by field to current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a ticket."""
        ticket = self.get_object()
        from core.enums import TicketStatus
        ticket.status = TicketStatus.RESOLVED.value
        ticket.resolution = request.data.get('resolution', ticket.resolution)
        from django.utils import timezone
        ticket.resolved_at = timezone.now()
        ticket.save()
        return Response(
            {'status': 'ticket resolved', 'id': ticket.id},
            status=status.HTTP_200_OK
        )
