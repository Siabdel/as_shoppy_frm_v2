"""
Stream & Milestone Serializers

Django REST Framework serializers for the streams and milestones API.
"""

from rest_framework import serializers

from .models import Stream, StreamEvent, Milestone, StreamSubscription, MilestoneComment
from .enums import StreamType, EventType, MilestoneStatus, MilestonePriority, SubscriptionType, EventImportance


class StreamSerializer(serializers.ModelSerializer):
    """Serializer for Stream model."""
    
    stream_type_display = serializers.CharField(
        source='stream_type.label',
        read_only=True
    )
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    content_object_type = serializers.CharField(
        source='content_type.model',
        read_only=True
    )
    
    class Meta:
        model = Stream
        fields = [
            'id', 'name', 'slug', 'description', 'stream_type',
            'stream_type_display', 'is_active', 'is_public',
            'event_count', 'subscriber_count', 'content_type',
            'object_id', 'content_object_type',
            'created_at', 'updated_at', 'last_event_at',
            'created_by', 'created_by_username'
        ]
        read_only_fields = [
            'slug', 'event_count', 'subscriber_count',
            'created_at', 'updated_at', 'last_event_at'
        ]


class StreamEventSerializer(serializers.ModelSerializer):
    """Serializer for StreamEvent model."""
    
    event_type_display = serializers.CharField(
        source='event_type.label',
        read_only=True
    )
    importance_display = serializers.CharField(
        source='importance.label',
        read_only=True
    )
    actor_username = serializers.CharField(
        source='actor.username',
        read_only=True
    )
    stream_name = serializers.CharField(
        source='stream.name',
        read_only=True
    )
    content_object_type = serializers.CharField(
        source='content_type.model',
        read_only=True
    )
    is_recent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = StreamEvent
        fields = [
            'id', 'stream', 'stream_name', 'event_type', 'event_type_display',
            'importance', 'importance_display', 'title', 'description',
            'actor', 'actor_username', 'actor_display',
            'content_type', 'object_id', 'content_object_type',
            'metadata', 'milestone', 'created_at', 'is_recent'
        ]
        read_only_fields = ['created_at']


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for Milestone model."""
    
    status_display = serializers.CharField(
        source='status.label',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='priority.label',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True
    )
    created_by_username = serializers.CharField(
        source='created_by.username',
        read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    actual_duration_days = serializers.IntegerField(read_only=True)
    can_start = serializers.SerializerMethodField()
    dependency_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'slug', 'description', 'status', 'status_display',
            'priority', 'priority_display', 'progress_percentage',
            'project', 'project_name', 'stream', 'assigned_to',
            'assigned_to_username', 'created_by', 'created_by_username',
            'planned_start_date', 'planned_end_date',
            'actual_start_date', 'actual_end_date',
            'is_overdue', 'days_remaining', 'duration_days', 'actual_duration_days',
            'budget', 'actual_cost', 'metadata',
            'can_start', 'dependency_ids',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'slug', 'is_overdue', 'days_remaining', 'duration_days',
            'actual_duration_days', 'created_at', 'updated_at', 'completed_at'
        ]
    
    def get_can_start(self, obj):
        """Check if milestone can be started."""
        return obj.can_start()
    
    def get_dependency_ids(self, obj):
        """Get list of dependency milestone IDs."""
        return [d.id for d in obj.dependencies.all()]


class MilestoneListSerializer(serializers.ModelSerializer):
    """Simplified serializer for milestone list views."""
    
    status_display = serializers.CharField(
        source='status.label',
        read_only=True
    )
    project_name = serializers.CharField(
        source='project.name',
        read_only=True
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'slug', 'status', 'status_display',
            'priority', 'progress_percentage',
            'project', 'project_name', 'assigned_to', 'assigned_to_username',
            'planned_end_date', 'is_overdue', 'days_remaining'
        ]


class MilestoneCommentSerializer(serializers.ModelSerializer):
    """Serializer for MilestoneComment model."""
    
    author_username = serializers.CharField(
        source='author.username',
        read_only=True
    )
    author_full_name = serializers.SerializerMethodField()
    milestone_name = serializers.CharField(
        source='milestone.name',
        read_only=True
    )
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MilestoneComment
        fields = [
            'id', 'milestone', 'milestone_name', 'author', 'author_username',
            'author_full_name', 'content', 'parent', 'is_edited', 'edited_at',
            'replies_count', 'created_at'
        ]
        read_only_fields = ['is_edited', 'edited_at', 'created_at']
    
    def get_author_full_name(self, obj):
        """Get author's full name."""
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return None
    
    def get_replies_count(self, obj):
        """Get number of replies to this comment."""
        return obj.replies.count()


class StreamSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for StreamSubscription model."""
    
    subscription_type_display = serializers.CharField(
        source='subscription_type.label',
        read_only=True
    )
    stream_name = serializers.CharField(
        source='stream.name',
        read_only=True
    )
    stream_slug = serializers.CharField(
        source='stream.slug',
        read_only=True
    )
    stream_type = serializers.CharField(
        source='stream.stream_type',
        read_only=True
    )
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    min_importance_display = serializers.CharField(
        source='min_importance.label',
        read_only=True
    )
    
    class Meta:
        model = StreamSubscription
        fields = [
            'id', 'stream', 'stream_name', 'stream_slug', 'stream_type',
            'user', 'username', 'subscription_type', 'subscription_type_display',
            'is_active', 'notify_email', 'notify_push', 'notify_sms',
            'min_importance', 'min_importance_display',
            'last_read_at', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StreamCreateEventSerializer(serializers.Serializer):
    """Serializer for creating stream events."""
    
    event_type = serializers.ChoiceField(
        choices=EventType.choices
    )
    description = serializers.CharField()
    title = serializers.CharField(required=False, allow_blank=True)
    importance = serializers.ChoiceField(
        choices=EventImportance.choices,
        default=EventImportance.NORMAL.value,
        required=False
    )
    metadata = serializers.JSONField(required=False, default=dict)


class MilestoneUpdateProgressSerializer(serializers.Serializer):
    """Serializer for updating milestone progress."""
    
    percentage = serializers.IntegerField(min_value=0, max_value=100)


class MilestoneCommentCreateSerializer(serializers.Serializer):
    """Serializer for creating milestone comments."""
    
    content = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)


class DashboardSerializer(serializers.Serializer):
    """Serializer for user dashboard data."""
    
    subscription_count = serializers.IntegerField()
    total_unread = serializers.IntegerField()
    recent_events = StreamEventSerializer(many=True)
    assigned_milestones = serializers.ListField(child=serializers.DictField())
    subscriptions = serializers.ListField(child=serializers.DictField())