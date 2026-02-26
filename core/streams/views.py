"""
Stream & Milestone API Views

RESTful API endpoints for streams and milestones management.
"""
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import (
    Stream, StreamEvent, Milestone,
    StreamSubscription, MilestoneComment
)
from .enums import (
    StreamType, EventType, MilestoneStatus,
    SubscriptionType, EventImportance
)
from .services import StreamService, MilestoneService, SubscriptionService
from .serializers import (
    StreamSerializer, StreamEventSerializer, MilestoneSerializer,
    MilestoneListSerializer, StreamSubscriptionSerializer,
    MilestoneCommentSerializer
)


class StreamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing streams.
    
    list: Get all streams
    create: Create a new stream
    retrieve: Get a specific stream by slug
    update: Update a stream
    partial_update: Partially update a stream
    destroy: Delete a stream
    """
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'last_event_at', 'event_count']
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filter streams based on user permissions."""
        queryset = Stream.objects.all()
        
        # Filter by type
        stream_type = self.request.query_params.get('type')
        if stream_type:
            queryset = queryset.filter(stream_type=stream_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by public status
        is_public = self.request.query_params.get('public')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        return queryset.select_related('created_by')
    
    @action(detail=True, methods=['post'])
    def add_event(self, request, slug=None):
        """Add an event to the stream."""
        stream = self.get_object()
        service = StreamService(user=request.user)
        
        event_type = request.data.get('event_type')
        description = request.data.get('description')
        importance = request.data.get('importance', EventImportance.NORMAL.value)
        metadata = request.data.get('metadata', {})
        
        if not event_type or not description:
            return Response(
                {'error': 'event_type and description are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            event_type_enum = EventType(event_type)
            importance_enum = EventImportance(importance)
        except ValueError:
            return Response(
                {'error': 'Invalid event_type or importance'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = service.add_event(
            stream_id=stream.id,
            event_type=event_type_enum,
            description=description,
            actor=request.user,
            importance=importance_enum,
            metadata=metadata
        )
        
        if result.success:
            return Response(
                StreamEventSerializer(result.data).data,
                status=status.HTTP_201_CREATED
            )
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def events(self, request, slug=None):
        """Get all events for a stream."""
        stream = self.get_object()
        events = stream.events.all()
        
        # Filter by event type
        event_type = request.query_params.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)
        
        # Filter by importance
        importance = request.query_params.get('importance')
        if importance:
            events = events.filter(importance=importance)
        
        serializer = StreamEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def recent_events(self, request, slug=None):
        """Get recent events for a stream."""
        stream = self.get_object()
        limit = int(request.query_params.get('limit', 20))
        events = stream.get_recent_events(limit=limit)
        serializer = StreamEventSerializer(events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def subscribe(self, request, slug=None):
        """Subscribe to a stream."""
        stream = self.get_object()
        service = SubscriptionService(user=request.user)
        
        sub_type = request.data.get('subscription_type', SubscriptionType.FOLLOW.value)
        try:
            sub_type_enum = SubscriptionType(sub_type)
        except ValueError:
            return Response(
                {'error': 'Invalid subscription_type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = service.subscribe(stream=stream, subscription_type=sub_type_enum)
        if result.success:
            return Response(
                StreamSubscriptionSerializer(result.data).data,
                status=status.HTTP_201_CREATED
            )
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unsubscribe(self, request, slug=None):
        """Unsubscribe from a stream."""
        stream = self.get_object()
        service = SubscriptionService(user=request.user)
        result = service.unsubscribe(stream=stream)
        
        if result.success:
            return Response({'status': 'unsubscribed'}, status=status.HTTP_200_OK)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)


class StreamEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing stream events (read-only).
    
    list: Get all events
    retrieve: Get a specific event
    """
    queryset = StreamEvent.objects.all()
    serializer_class = StreamEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'title']
    ordering_fields = ['created_at', 'importance']
    
    def get_queryset(self):
        """Filter events based on query parameters."""
        queryset = StreamEvent.objects.all()
        
        # Filter by stream
        stream_id = self.request.query_params.get('stream')
        if stream_id:
            queryset = queryset.filter(stream_id=stream_id)
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by actor
        actor_id = self.request.query_params.get('actor')
        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)
        
        # Filter by importance
        importance = self.request.query_params.get('importance')
        if importance:
            queryset = queryset.filter(importance=importance)
        
        return queryset.select_related('stream', 'actor')


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing milestones.
    
    list: Get all milestones
    create: Create a new milestone
    retrieve: Get a specific milestone
    update: Update a milestone
    partial_update: Partially update a milestone
    destroy: Delete a milestone
    """
    queryset = Milestone.objects.all()
    serializer_class = MilestoneSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'planned_end_date', 'priority', 'progress_percentage']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return MilestoneListSerializer
        return MilestoneSerializer
    
    def get_queryset(self):
        """Filter milestones based on query parameters."""
        queryset = Milestone.objects.all()
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by project
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by assignee
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to__username=assigned_to)
        
        return queryset.select_related('project', 'assigned_to', 'created_by')
    
    def perform_create(self, serializer):
        """Set the created_by field to current user."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, slug=None):
        """Mark milestone as started."""
        milestone = self.get_object()
        service = MilestoneService(user=request.user)
        result = service.start_milestone(milestone_id=milestone.id)
        
        if result.success:
            return Response(MilestoneSerializer(result.data).data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, slug=None):
        """Mark milestone as completed."""
        milestone = self.get_object()
        service = MilestoneService(user=request.user)
        result = service.complete_milestone(milestone_id=milestone.id)
        
        if result.success:
            return Response(MilestoneSerializer(result.data).data)
        return Response({'error': result.error}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, slug=None):
        """Update milestone progress percentage."""
        milestone = self.get_object()
        progress = request.data.get('progress_percentage')
        
        if progress is None:
            return Response(
                {'error': 'progress_percentage is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            progress = int(progress)
            if not 0 <= progress <= 100:
                raise ValueError
        except ValueError:
            return Response(
                {'error': 'progress_percentage must be an integer between 0 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        milestone.progress_percentage = progress
        milestone.save()
        return Response(MilestoneSerializer(milestone).data)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, slug=None):
        """Get all comments for a milestone."""
        milestone = self.get_object()
        comments = milestone.comments.all()
        serializer = MilestoneCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, slug=None):
        """Add a comment to a milestone."""
        milestone = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = MilestoneComment.objects.create(
            milestone=milestone,
            author=request.user,
            content=content
        )
        return Response(
            MilestoneCommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def add_dependency(self, request, slug=None):
        """Add a dependency to this milestone."""
        milestone = self.get_object()
        dependency_id = request.data.get('dependency_id')
        
        if not dependency_id:
            return Response(
                {'error': 'dependency_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dependency = Milestone.objects.get(id=dependency_id)
            milestone.dependencies.add(dependency)
            return Response({'status': 'dependency added'})
        except Milestone.DoesNotExist:
            return Response(
                {'error': 'Milestone not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, slug=None):
        """Remove a dependency from this milestone."""
        milestone = self.get_object()
        dependency_id = request.data.get('dependency_id')
        
        if not dependency_id:
            return Response(
                {'error': 'dependency_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dependency = Milestone.objects.get(id=dependency_id)
            milestone.dependencies.remove(dependency)
            return Response({'status': 'dependency removed'})
        except Milestone.DoesNotExist:
            return Response(
                {'error': 'Milestone not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class StreamSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stream subscriptions.
    
    list: Get all subscriptions for current user
    create: Create a new subscription
    retrieve: Get a specific subscription
    update: Update a subscription
    destroy: Delete a subscription
    """
    serializer_class = StreamSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return subscriptions for current user only."""
        return StreamSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Set the user to current user."""
        serializer.save(user=self.request.user)


class MilestoneCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing milestone comments.
    
    list: Get all comments
    create: Create a new comment
    retrieve: Get a specific comment
    update: Update a comment
    destroy: Delete a comment
    """
    queryset = MilestoneComment.objects.all()
    serializer_class = MilestoneCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Filter comments based on query parameters."""
        queryset = MilestoneComment.objects.all()
        
        # Filter by milestone
        milestone_id = self.request.query_params.get('milestone')
        if milestone_id:
            queryset = queryset.filter(milestone_id=milestone_id)
        
        # Filter by author
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        return queryset.select_related('milestone', 'author')
    
    def perform_create(self, serializer):
        """Set the author to current user."""
        serializer.save(author=self.request.user)
