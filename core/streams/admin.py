"""
Stream & Milestone Admin Configuration
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Stream, StreamEvent, Milestone, StreamSubscription, MilestoneComment
from .enums import EventImportance, MilestoneStatus


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    """Admin configuration for Stream model."""
    
    list_display = [
        'name', 'stream_type', 'is_active', 'event_count',
        'subscriber_count', 'last_event_at', 'created_at'
    ]
    list_filter = ['stream_type', 'is_active', 'is_public', 'created_at']
    search_fields = ['name', 'description', 'slug']
    readonly_fields = [
        'slug', 'event_count', 'subscriber_count',
        'created_at', 'updated_at', 'last_event_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Type & Status'), {
            'fields': ('stream_type', 'is_active', 'is_public')
        }),
        (_('Content Object'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Statistics'), {
            'fields': ('event_count', 'subscriber_count', 'last_event_at'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )


class EventImportanceListFilter(admin.SimpleListFilter):
    """Custom filter for event importance."""
    
    title = _('Importance')
    parameter_name = 'importance'
    
    def lookups(self, request, model_admin):
        return EventImportance.choices
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(importance=self.value())
        return queryset


@admin.register(StreamEvent)
class StreamEventAdmin(admin.ModelAdmin):
    """Admin configuration for StreamEvent model."""
    
    list_display = [
        'event_type', 'importance_badge', 'stream', 'actor',
        'created_at', 'is_recent'
    ]
    list_filter = ['event_type', EventImportanceListFilter, 'created_at']
    search_fields = ['description', 'title', 'actor_display']
    readonly_fields = ['created_at', 'is_recent']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('stream', 'event_type', 'importance')
        }),
        (_('Content'), {
            'fields': ('title', 'description')
        }),
        (_('Actor'), {
            'fields': ('actor', 'actor_display')
        }),
        (_('Related Object'), {
            'fields': ('content_type', 'object_id', 'milestone'),
            'classes': ('collapse',)
        }),
        (_('Data'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def importance_badge(self, obj):
        """Display importance as a colored badge."""
        colors = {
            EventImportance.LOW.value: 'gray',
            EventImportance.NORMAL.value: 'blue',
            EventImportance.HIGH.value: 'orange',
            EventImportance.CRITICAL.value: 'red',
        }
        color = colors.get(obj.importance.value, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.importance.label
        )
    importance_badge.short_description = _('Importance')
    
    def is_recent(self, obj):
        """Display if event is recent."""
        return obj.is_recent
    is_recent.boolean = True
    is_recent.short_description = _('Recent')


class MilestoneStatusListFilter(admin.SimpleListFilter):
    """Custom filter for milestone status."""
    
    title = _('Status')
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return MilestoneStatus.choices
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    """Admin configuration for Milestone model."""
    
    list_display = [
        'name', 'project', 'status_badge', 'priority',
        'progress_bar', 'is_overdue', 'planned_end_date'
    ]
    list_filter = [
        MilestoneStatusListFilter, 'priority',
        'created_at', 'planned_end_date'
    ]
    search_fields = ['name', 'description', 'slug', 'project__name']
    readonly_fields = [
        'slug', 'is_overdue', 'days_remaining',
        'duration_days', 'actual_duration_days',
        'created_at', 'updated_at', 'completed_at'
    ]
    date_hierarchy = 'planned_end_date'
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Status & Priority'), {
            'fields': ('status', 'priority', 'progress_percentage')
        }),
        (_('Timeline'), {
            'fields': (
                'planned_start_date', 'planned_end_date',
                'actual_start_date', 'actual_end_date'
            )
        }),
        (_('Calculated Fields'), {
            'fields': (
                'is_overdue', 'days_remaining',
                'duration_days', 'actual_duration_days'
            ),
            'classes': ('collapse',)
        }),
        (_('Relations'), {
            'fields': ('project', 'stream', 'dependencies', 'assigned_to')
        }),
        (_('Financial'), {
            'fields': ('budget', 'actual_cost'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at', 'created_by'),
            'classes': ('collapse',)
        }),
        (_('Additional Data'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['dependencies']
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            MilestoneStatus.PENDING.value: 'gray',
            MilestoneStatus.PLANNED.value: 'blue',
            MilestoneStatus.IN_PROGRESS.value: 'orange',
            MilestoneStatus.COMPLETED.value: 'green',
            MilestoneStatus.DELAYED.value: 'red',
            MilestoneStatus.CANCELLED.value: 'darkgray',
            MilestoneStatus.ON_HOLD.value: 'purple',
        }
        color = colors.get(obj.status.value, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.status.label
        )
    status_badge.short_description = _('Status')
    
    def progress_bar(self, obj):
        """Display progress as a visual bar."""
        return format_html(
            '<div style="width: 100px; background-color: #e0e0e0; '
            'border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: #4CAF50; height: 20px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%</div></div>',
            obj.progress_percentage, obj.progress_percentage
        )
    progress_bar.short_description = _('Progress')
    
    def is_overdue(self, obj):
        """Display overdue status."""
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = _('Overdue')


@admin.register(StreamSubscription)
class StreamSubscriptionAdmin(admin.ModelAdmin):
    """Admin configuration for StreamSubscription model."""
    
    list_display = [
        'user', 'stream', 'subscription_type', 'is_active',
        'unread_count', 'created_at'
    ]
    list_filter = ['subscription_type', 'is_active', 'notify_email', 'created_at']
    search_fields = ['user__username', 'user__email', 'stream__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('stream', 'user', 'subscription_type', 'is_active')
        }),
        (_('Notifications'), {
            'fields': ('notify_email', 'notify_push', 'notify_sms', 'min_importance')
        }),
        (_('Read Tracking'), {
            'fields': ('last_read_at', 'unread_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MilestoneComment)
class MilestoneCommentAdmin(admin.ModelAdmin):
    """Admin configuration for MilestoneComment model."""
    
    list_display = ['milestone', 'author', 'content_preview', 'created_at']
    list_filter = ['created_at', 'is_edited']
    search_fields = ['content', 'author__username', 'milestone__name']
    readonly_fields = ['created_at', 'edited_at']
    
    fieldsets = (
        (None, {
            'fields': ('milestone', 'author', 'content')
        }),
        (_('Threading'), {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        (_('Edit Info'), {
            'fields': ('is_edited', 'edited_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Display a preview of the comment content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('Content Preview')