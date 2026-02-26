"""
Streams & Milestones Models

Provides comprehensive activity stream and milestone tracking functionality.
"""

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.enums import ChoiceEnumField
from .enums import (
    StreamType, EventType, MilestoneStatus, MilestonePriority,
    SubscriptionType, EventImportance
)


class Stream(models.Model):
    """
    A stream represents a sequence of events related to a specific object
    (project, order, user, etc.). Streams can be followed by users who
    want to stay updated on changes.
    """
    
    name = models.CharField(
        max_length=255,
        verbose_name=_('Stream Name')
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_('Slug')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Stream type categorization
    stream_type = ChoiceEnumField(
        enum_type=StreamType,
        default=StreamType.PROJECT,
        verbose_name=_('Stream Type')
    )
    
    # Generic relation to the object this stream belongs to
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Content Type')
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Object ID')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Stream settings
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Is Public')
    )
    
    # Statistics (denormalized for performance)
    event_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Event Count')
    )
    subscriber_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Subscriber Count')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    last_event_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Event At')
    )
    
    # Relations
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_streams',
        verbose_name=_('Created By')
    )
    
    class Meta:
        verbose_name = _('Stream')
        verbose_name_plural = _('Streams')
        ordering = ['-last_event_at', '-created_at']
        indexes = [
            models.Index(fields=['stream_type', 'is_active']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['slug']),
            models.Index(fields=['last_event_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.stream_type})"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Stream.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def update_event_count(self):
        """Update the cached event count."""
        self.event_count = self.events.count()
        self.save(update_fields=['event_count'])
    
    def update_subscriber_count(self):
        """Update the cached subscriber count."""
        self.subscriber_count = self.subscriptions.filter(
            is_active=True
        ).count()
        self.save(update_fields=['subscriber_count'])
    
    def get_recent_events(self, limit=20):
        """Get recent events for this stream."""
        return self.events.select_related('actor').order_by('-created_at')[:limit]
    
    def add_event(self, event_type, description, actor=None, 
                  importance=None, metadata=None, content_object=None):
        """Add a new event to this stream."""
        event = StreamEvent.objects.create(
            stream=self,
            event_type=event_type,
            description=description,
            actor=actor,
            importance=importance or EventImportance.NORMAL,
            metadata=metadata or {},
            content_object=content_object
        )
        
        # Update stream statistics
        self.last_event_at = timezone.now()
        self.update_event_count()
        
        return event


class StreamEvent(models.Model):
    """
    Represents a single event in a stream. Events are immutable records
    of actions or changes that occurred.
    """
    
    stream = models.ForeignKey(
        Stream,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('Stream')
    )
    
    # Event classification
    event_type = ChoiceEnumField(
        enum_type=EventType,
        verbose_name=_('Event Type')
    )
    importance = ChoiceEnumField(
        enum_type=EventImportance,
        default=EventImportance.NORMAL,
        verbose_name=_('Importance')
    )
    
    # Event content
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Title')
    )
    description = models.TextField(
        verbose_name=_('Description')
    )
    
    # Actor who performed the action
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stream_events',
        verbose_name=_('Actor')
    )
    actor_display = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Actor Display Name')
    )
    
    # Generic relation to the object this event relates to
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Content Type')
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Object ID')
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    # Optional: link to a milestone
    milestone = models.ForeignKey(
        'Milestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name=_('Related Milestone')
    )
    
    class Meta:
        verbose_name = _('Stream Event')
        verbose_name_plural = _('Stream Events')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stream', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['importance', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        """Set actor display name before saving."""
        if self.actor and not self.actor_display:
            self.actor_display = self.actor.get_full_name() or self.actor.username
        super().save(*args, **kwargs)
    
    @property
    def is_recent(self):
        """Check if event is recent (within last 24 hours)."""
        if not self.created_at:
            return False
        return (timezone.now() - self.created_at).total_seconds() < 86400


class Milestone(models.Model):
    """
    A milestone represents a significant point or goal in a project timeline.
    Milestones can have dependencies and track progress.
    """
    
    # Identification
    name = models.CharField(
        max_length=255,
        verbose_name=_('Milestone Name')
    )
    slug = models.SlugField(
        max_length=255,
        blank=True,
        verbose_name=_('Slug')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Status and priority
    status = ChoiceEnumField(
        enum_type=MilestoneStatus,
        default=MilestoneStatus.PENDING,
        verbose_name=_('Status')
    )
    priority = ChoiceEnumField(
        enum_type=MilestonePriority,
        default=MilestonePriority.MEDIUM,
        verbose_name=_('Priority')
    )
    
    # Timeline
    planned_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Planned Start Date')
    )
    planned_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Planned End Date')
    )
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Actual Start Date')
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Actual End Date')
    )
    
    # Progress tracking
    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Progress %')
    )
    
    # Relations
    project = models.ForeignKey(
        'project.Project',
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name=_('Project')
    )
    stream = models.ForeignKey(
        Stream,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='milestones',
        verbose_name=_('Associated Stream')
    )
    
    # Dependencies (self-referential many-to-many)
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_milestones',
        verbose_name=_('Dependencies')
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_milestones',
        verbose_name=_('Assigned To')
    )
    
    # Responsible parties
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_milestones',
        verbose_name=_('Created By')
    )
    
    # Financial data
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Budget')
    )
    actual_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Actual Cost')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed At')
    )
    
    # Additional data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata')
    )
    
    class Meta:
        verbose_name = _('Milestone')
        verbose_name_plural = _('Milestones')
        ordering = ['planned_end_date', 'priority', 'created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['status', 'planned_end_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
        unique_together = [['project', 'slug']]
    
    def __str__(self):
        return f"{self.name} ({self.project.name})"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and handle completion."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Milestone.objects.filter(
                project=self.project,
                slug=slug
            ).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Handle completion timestamp
        if self.status == MilestoneStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
            self.progress_percentage = 100
        elif self.status != MilestoneStatus.COMPLETED and self.completed_at:
            self.completed_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if milestone is overdue."""
        if self.status in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
            return False
        if not self.planned_end_date:
            return False
        return timezone.now().date() > self.planned_end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining until planned end date."""
        if not self.planned_end_date:
            return None
        delta = self.planned_end_date - timezone.now().date()
        return delta.days
    
    @property
    def duration_days(self):
        """Calculate planned duration in days."""
        if not self.planned_start_date or not self.planned_end_date:
            return None
        return (self.planned_end_date - self.planned_start_date).days
    
    @property
    def actual_duration_days(self):
        """Calculate actual duration in days."""
        if not self.actual_start_date:
            return None
        end = self.actual_end_date or timezone.now().date()
        return (end - self.actual_start_date).days
    
    def update_progress(self, percentage):
        """Update milestone progress percentage."""
        self.progress_percentage = max(0, min(100, percentage))
        if self.progress_percentage == 100:
            self.status = MilestoneStatus.COMPLETED
        elif self.progress_percentage > 0:
            self.status = MilestoneStatus.IN_PROGRESS
        self.save()
    
    def start(self):
        """Start the milestone."""
        self.status = MilestoneStatus.IN_PROGRESS
        self.actual_start_date = timezone.now().date()
        self.save()
        
        # Create stream event if stream exists
        if self.stream:
            self.stream.add_event(
                event_type=EventType.MILESTONE_STARTED,
                description=f"Milestone '{self.name}' has started",
                content_object=self
            )
    
    def complete(self):
        """Complete the milestone."""
        self.status = MilestoneStatus.COMPLETED
        self.progress_percentage = 100
        self.actual_end_date = timezone.now().date()
        self.save()
        
        # Create stream event if stream exists
        if self.stream:
            self.stream.add_event(
                event_type=EventType.MILESTONE_COMPLETED,
                description=f"Milestone '{self.name}' has been completed",
                content_object=self
            )
    
    def can_start(self):
        """Check if milestone can be started (dependencies met)."""
        if self.status != MilestoneStatus.PENDING:
            return False
        # Check all dependencies are completed
        incomplete_deps = self.dependencies.exclude(
            status=MilestoneStatus.COMPLETED
        )
        return not incomplete_deps.exists()
    
    def get_blocked_milestones(self):
        """Get milestones that are blocked by this one."""
        return self.dependent_milestones.all()


class StreamSubscription(models.Model):
    """
    Represents a user's subscription to a stream. Users can follow
    streams to receive notifications and updates.
    """
    
    stream = models.ForeignKey(
        Stream,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('Stream')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stream_subscriptions',
        verbose_name=_('User')
    )
    
    # Subscription settings
    subscription_type = ChoiceEnumField(
        enum_type=SubscriptionType,
        default=SubscriptionType.FOLLOW,
        verbose_name=_('Subscription Type')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )
    
    # Notification preferences
    notify_email = models.BooleanField(
        default=True,
        verbose_name=_('Email Notifications')
    )
    notify_push = models.BooleanField(
        default=False,
        verbose_name=_('Push Notifications')
    )
    notify_sms = models.BooleanField(
        default=False,
        verbose_name=_('SMS Notifications')
    )
    
    # Filtering
    min_importance = ChoiceEnumField(
        enum_type=EventImportance,
        default=EventImportance.NORMAL,
        verbose_name=_('Minimum Importance')
    )
    
    # Read tracking
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Last Read At')
    )
    unread_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Unread Count')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Subscribed At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    
    class Meta:
        verbose_name = _('Stream Subscription')
        verbose_name_plural = _('Stream Subscriptions')
        unique_together = [['stream', 'user']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['stream', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user} -> {self.stream}"
    
    def mark_as_read(self):
        """Mark all events as read."""
        self.last_read_at = timezone.now()
        self.unread_count = 0
        self.save(update_fields=['last_read_at', 'unread_count'])
    
    def increment_unread(self, count=1):
        """Increment unread count."""
        self.unread_count += count
        self.save(update_fields=['unread_count'])
    
    def get_unread_events(self):
        """Get unread events for this subscription."""
        if not self.last_read_at:
            return self.stream.events.all()
        return self.stream.events.filter(created_at__gt=self.last_read_at)


class MilestoneComment(models.Model):
    """
    Comments on milestones for team communication and updates.
    """
    
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('Milestone')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='milestone_comments',
        verbose_name=_('Author')
    )
    content = models.TextField(
        verbose_name=_('Content')
    )
    
    # For threaded comments
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('Parent Comment')
    )
    
    # Metadata
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_('Is Edited')
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Edited At')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    class Meta:
        verbose_name = _('Milestone Comment')
        verbose_name_plural = _('Milestone Comments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.milestone}"
    
    def edit(self, new_content):
        """Edit the comment content."""
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save()