"""
Stream & Milestone Services

Business logic layer for the streams and milestones system.
"""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta

from django.db import transaction
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from core.services.base import BaseService, ServiceResult, ValidationError
from .models import Stream, StreamEvent, Milestone, StreamSubscription, MilestoneComment
from .enums import (
    StreamType, EventType, MilestoneStatus, MilestonePriority,
    SubscriptionType, EventImportance
)


class StreamService(BaseService):
    """
    Service for managing streams and their events.
    """
    
    model_class = Stream
    
    def validate(self, data: Dict[str, Any], instance: Optional[Any] = None) -> Dict[str, Any]:
        """Validate stream data."""
        errors = {}
        
        if not data.get('name'):
            errors['name'] = "Stream name is required"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def get_or_create_for_object(self, obj, stream_type: StreamType = None, 
                                  name: str = None) -> Stream:
        """Get or create a stream for any object."""
        content_type = ContentType.objects.get_for_model(obj)
        
        defaults = {
            'name': name or f"Stream for {obj}",
            'stream_type': stream_type or StreamType.SYSTEM,
            'is_active': True
        }
        
        stream, created = self.model_class.objects.get_or_create(
            content_type=content_type,
            object_id=obj.pk,
            defaults=defaults
        )
        
        return stream
    
    def add_event(self, stream_id: int, event_type: EventType, 
                  description: str, actor=None, importance: EventImportance = None,
                  metadata: Dict = None, content_object=None) -> ServiceResult:
        """Add an event to a stream."""
        stream = self.get_by_id(stream_id)
        if not stream:
            return ServiceResult.fail(f"Stream {stream_id} not found")
        
        try:
            event = stream.add_event(
                event_type=event_type,
                description=description,
                actor=actor,
                importance=importance or EventImportance.NORMAL,
                metadata=metadata or {},
                content_object=content_object
            )
            
            # Notify subscribers
            self._notify_subscribers(stream, event)
            
            return ServiceResult.ok(event, "Event added successfully")
        except Exception as e:
            return ServiceResult.fail(f"Failed to add event: {str(e)}")
    
    def _notify_subscribers(self, stream: Stream, event: StreamEvent):
        """Notify stream subscribers about a new event."""
        subscriptions = stream.subscriptions.filter(
            is_active=True
        ).select_related('user')
        
        for sub in subscriptions:
            # Check importance threshold
            importance_levels = {
                EventImportance.LOW.value: 1,
                EventImportance.NORMAL.value: 2,
                EventImportance.HIGH.value: 3,
                EventImportance.CRITICAL.value: 4
            }
            
            event_level = importance_levels.get(event.importance.value, 2)
            min_level = importance_levels.get(sub.min_importance.value, 2)
            
            if event_level >= min_level:
                sub.increment_unread()
                
                # TODO: Send actual notifications (email, push, sms)
                # based on subscription preferences
    
    def get_user_stream_feed(self, user, limit: int = 50) -> ServiceResult:
        """Get aggregated feed for a user from all subscribed streams."""
        subscribed_stream_ids = StreamSubscription.objects.filter(
            user=user,
            is_active=True
        ).values_list('stream_id', flat=True)
        
        events = StreamEvent.objects.filter(
            stream_id__in=subscribed_stream_ids
        ).select_related('stream', 'actor').order_by('-created_at')[:limit]
        
        return ServiceResult.ok(list(events))
    
    def get_unread_counts(self, user) -> Dict[int, int]:
        """Get unread event counts for all user's subscriptions."""
        subscriptions = StreamSubscription.objects.filter(
            user=user,
            is_active=True
        )
        
        return {sub.stream_id: sub.unread_count for sub in subscriptions}
    
    def search_events(self, query: str, stream_type: StreamType = None,
                      limit: int = 50) -> ServiceResult:
        """Search events by description or metadata."""
        events = StreamEvent.objects.filter(
            Q(description__icontains=query) |
            Q(title__icontains=query)
        )
        
        if stream_type:
            events = events.filter(stream__stream_type=stream_type)
        
        events = events.select_related('stream', 'actor').order_by('-created_at')[:limit]
        
        return ServiceResult.ok(list(events))


class MilestoneService(BaseService):
    """
    Service for managing milestones.
    """
    
    model_class = Milestone
    
    def validate(self, data: Dict[str, Any], instance: Optional[Any] = None) -> Dict[str, Any]:
        """Validate milestone data."""
        errors = {}
        
        if not data.get('name'):
            errors['name'] = "Milestone name is required"
        
        if not data.get('project_id'):
            errors['project'] = "Project is required"
        
        # Validate dates
        planned_start = data.get('planned_start_date')
        planned_end = data.get('planned_end_date')
        
        if planned_start and planned_end and planned_start > planned_end:
            errors['planned_end_date'] = "End date must be after start date"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def perform_create(self, validated_data: Dict[str, Any]) -> Any:
        """Create milestone and associated stream."""
        from project.models import Project
        
        project_id = validated_data.pop('project_id', None)
        if project_id:
            validated_data['project'] = Project.objects.get(id=project_id)
        
        # Create the milestone
        milestone = super().perform_create(validated_data)
        
        # Create associated stream
        stream = Stream.objects.create(
            name=f"Milestone: {milestone.name}",
            stream_type=StreamType.MILESTONE,
            content_object=milestone,
            created_by=validated_data.get('created_by')
        )
        
        milestone.stream = stream
        milestone.save(update_fields=['stream'])
        
        # Add creation event
        stream.add_event(
            event_type=EventType.MILESTONE_CREATED,
            description=f"Milestone '{milestone.name}' was created",
            content_object=milestone
        )
        
        return milestone
    
    def start_milestone(self, milestone_id: int, user=None) -> ServiceResult:
        """Start a milestone."""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return ServiceResult.fail(f"Milestone {milestone_id} not found")
        
        if not milestone.can_start():
            incomplete_deps = milestone.dependencies.exclude(
                status=MilestoneStatus.COMPLETED
            )
            dep_names = [d.name for d in incomplete_deps]
            return ServiceResult.fail(
                f"Cannot start milestone. Incomplete dependencies: {dep_names}"
            )
        
        try:
            milestone.start()
            return ServiceResult.ok(milestone, "Milestone started successfully")
        except Exception as e:
            return ServiceResult.fail(f"Failed to start milestone: {str(e)}")
    
    def complete_milestone(self, milestone_id: int, user=None) -> ServiceResult:
        """Complete a milestone."""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return ServiceResult.fail(f"Milestone {milestone_id} not found")
        
        try:
            milestone.complete()
            
            # Unlock dependent milestones
            blocked = milestone.get_blocked_milestones()
            for dep in blocked:
                if dep.can_start():
                    # Optionally auto-start or notify
                    pass
            
            return ServiceResult.ok(milestone, "Milestone completed successfully")
        except Exception as e:
            return ServiceResult.fail(f"Failed to complete milestone: {str(e)}")
    
    def update_progress(self, milestone_id: int, percentage: int) -> ServiceResult:
        """Update milestone progress."""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return ServiceResult.fail(f"Milestone {milestone_id} not found")
        
        try:
            milestone.update_progress(percentage)
            return ServiceResult.ok(milestone, "Progress updated successfully")
        except Exception as e:
            return ServiceResult.fail(f"Failed to update progress: {str(e)}")
    
    def get_project_timeline(self, project_id: int) -> ServiceResult:
        """Get complete timeline for a project including all milestones."""
        milestones = self.get_queryset().filter(
            project_id=project_id
        ).order_by('planned_start_date')
        
        timeline_data = {
            'milestones': [],
            'statistics': {
                'total': milestones.count(),
                'completed': milestones.filter(
                    status=MilestoneStatus.COMPLETED
                ).count(),
                'in_progress': milestones.filter(
                    status=MilestoneStatus.IN_PROGRESS
                ).count(),
                'pending': milestones.filter(
                    status=MilestoneStatus.PENDING
                ).count(),
                'overdue': sum(1 for m in milestones if m.is_overdue)
            },
            'progress': self._calculate_project_progress(milestones)
        }
        
        for ms in milestones:
            timeline_data['milestones'].append({
                'id': ms.id,
                'name': ms.name,
                'status': ms.status.value,
                'priority': ms.priority.value,
                'progress': ms.progress_percentage,
                'planned_start': ms.planned_start_date,
                'planned_end': ms.planned_end_date,
                'actual_start': ms.actual_start_date,
                'actual_end': ms.actual_end_date,
                'is_overdue': ms.is_overdue,
                'days_remaining': ms.days_remaining,
                'dependencies': [d.id for d in ms.dependencies.all()]
            })
        
        return ServiceResult.ok(timeline_data)
    
    def _calculate_project_progress(self, milestones) -> Dict[str, Any]:
        """Calculate overall project progress based on milestones."""
        total = milestones.count()
        if total == 0:
            return {'percentage': 0, 'weighted_percentage': 0}
        
        completed = milestones.filter(status=MilestoneStatus.COMPLETED).count()
        in_progress = milestones.filter(status=MilestoneStatus.IN_PROGRESS)
        
        # Simple percentage
        simple_pct = (completed / total) * 100
        
        # Weighted percentage (considering progress of in-progress milestones)
        total_progress = sum(m.progress_percentage for m in milestones)
        weighted_pct = total_progress / total
        
        return {
            'percentage': round(simple_pct, 2),
            'weighted_percentage': round(weighted_pct, 2),
            'completed_count': completed,
            'total_count': total
        }
    
    def get_critical_path(self, project_id: int) -> ServiceResult:
        """Identify critical path milestones for a project."""
        milestones = self.get_queryset().filter(
            project_id=project_id,
            status__in=[
                MilestoneStatus.PENDING.value,
                MilestoneStatus.PLANNED.value,
                MilestoneStatus.IN_PROGRESS.value
            ]
        )
        
        # Find milestones with no incomplete dependencies
        # (can be started immediately)
        critical = []
        for ms in milestones:
            incomplete_deps = ms.dependencies.exclude(
                status=MilestoneStatus.COMPLETED
            )
            if not incomplete_deps.exists():
                critical.append(ms)
        
        return ServiceResult.ok({
            'critical_milestones': [
                {'id': m.id, 'name': m.name, 'priority': m.priority.value}
                for m in critical
            ]
        })
    
    def add_comment(self, milestone_id: int, user, content: str,
                    parent_id: int = None) -> ServiceResult:
        """Add a comment to a milestone."""
        milestone = self.get_by_id(milestone_id)
        if not milestone:
            return ServiceResult.fail(f"Milestone {milestone_id} not found")
        
        try:
            comment_data = {
                'milestone': milestone,
                'author': user,
                'content': content
            }
            
            if parent_id:
                comment_data['parent_id'] = parent_id
            
            comment = MilestoneComment.objects.create(**comment_data)
            
            # Add to stream
            if milestone.stream:
                milestone.stream.add_event(
                    event_type=EventType.TASK_COMMENTED,
                    description=f"New comment on milestone '{milestone.name}'",
                    actor=user,
                    content_object=milestone
                )
            
            return ServiceResult.ok(comment, "Comment added successfully")
        except Exception as e:
            return ServiceResult.fail(f"Failed to add comment: {str(e)}")


class SubscriptionService(BaseService):
    """
    Service for managing stream subscriptions.
    """
    
    model_class = StreamSubscription
    
    def subscribe(self, user, stream_id: int, 
                  subscription_type: SubscriptionType = None) -> ServiceResult:
        """Subscribe a user to a stream."""
        try:
            stream = Stream.objects.get(id=stream_id)
        except Stream.DoesNotExist:
            return ServiceResult.fail(f"Stream {stream_id} not found")
        
        subscription, created = self.model_class.objects.get_or_create(
            user=user,
            stream=stream,
            defaults={
                'subscription_type': subscription_type or SubscriptionType.FOLLOW,
                'is_active': True
            }
        )
        
        if not created:
            subscription.is_active = True
            if subscription_type:
                subscription.subscription_type = subscription_type
            subscription.save()
        
        # Update subscriber count
        stream.update_subscriber_count()
        
        return ServiceResult.ok(
            subscription,
            "Subscribed successfully" if created else "Subscription reactivated"
        )
    
    def unsubscribe(self, user, stream_id: int) -> ServiceResult:
        """Unsubscribe a user from a stream."""
        try:
            subscription = self.model_class.objects.get(
                user=user,
                stream_id=stream_id
            )
            subscription.is_active = False
            subscription.save()
            
            # Update subscriber count
            subscription.stream.update_subscriber_count()
            
            return ServiceResult.ok(None, "Unsubscribed successfully")
        except self.model_class.DoesNotExist:
            return ServiceResult.fail("Subscription not found")
    
    def mark_stream_as_read(self, user, stream_id: int) -> ServiceResult:
        """Mark all events in a stream as read for a user."""
        try:
            subscription = self.model_class.objects.get(
                user=user,
                stream_id=stream_id,
                is_active=True
            )
            subscription.mark_as_read()
            return ServiceResult.ok(None, "Marked as read")
        except self.model_class.DoesNotExist:
            return ServiceResult.fail("Subscription not found")
    
    def get_user_dashboard(self, user) -> ServiceResult:
        """Get comprehensive dashboard data for a user."""
        # Get subscriptions
        subscriptions = self.model_class.objects.filter(
            user=user,
            is_active=True
        ).select_related('stream')
        
        total_unread = sum(sub.unread_count for sub in subscriptions)
        
        # Get recent events from subscribed streams
        stream_ids = [sub.stream_id for sub in subscriptions]
        recent_events = StreamEvent.objects.filter(
            stream_id__in=stream_ids
        ).select_related('stream', 'actor').order_by('-created_at')[:10]
        
        # Get milestones assigned to user
        assigned_milestones = Milestone.objects.filter(
            assigned_to=user
        ).exclude(status=MilestoneStatus.COMPLETED).order_by('planned_end_date')[:5]
        
        return ServiceResult.ok({
            'subscription_count': subscriptions.count(),
            'total_unread': total_unread,
            'recent_events': [
                {
                    'id': e.id,
                    'type': e.event_type.value,
                    'description': e.description,
                    'stream': e.stream.name,
                    'created_at': e.created_at
                }
                for e in recent_events
            ],
            'assigned_milestones': [
                {
                    'id': m.id,
                    'name': m.name,
                    'project': m.project.name,
                    'status': m.status.value,
                    'due_date': m.planned_end_date,
                    'is_overdue': m.is_overdue
                }
                for m in assigned_milestones
            ],
            'subscriptions': [
                {
                    'stream_id': sub.stream_id,
                    'stream_name': sub.stream.name,
                    'type': sub.subscription_type.value,
                    'unread_count': sub.unread_count
                }
                for sub in subscriptions
            ]
        })