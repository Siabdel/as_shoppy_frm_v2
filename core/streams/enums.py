"""
Stream & Milestone Enumerations

Defines all enum types used in the streams and milestones system.
"""

from core.enums import ChoiceEnum, _


class StreamType(ChoiceEnum):
    """Types of streams in the system."""
    PROJECT = 'project', _('Project Stream')
    ORDER = 'order', _('Order Stream')
    USER = 'user', _('User Activity Stream')
    SYSTEM = 'system', _('System Stream')
    MILESTONE = 'milestone', _('Milestone Stream')
    PRODUCT = 'product', _('Product Stream')


class EventType(ChoiceEnum):
    """Types of events that can occur in streams."""
    # Project events
    PROJECT_CREATED = 'project_created', _('Project Created')
    PROJECT_UPDATED = 'project_updated', _('Project Updated')
    PROJECT_STATUS_CHANGED = 'project_status_changed', _('Status Changed')
    PROJECT_PHASE_STARTED = 'project_phase_started', _('Phase Started')
    PROJECT_COMPLETED = 'project_completed', _('Project Completed')
    
    # Milestone events
    MILESTONE_CREATED = 'milestone_created', _('Milestone Created')
    MILESTONE_STARTED = 'milestone_started', _('Milestone Started')
    MILESTONE_COMPLETED = 'milestone_completed', _('Milestone Completed')
    MILESTONE_DELAYED = 'milestone_delayed', _('Milestone Delayed')
    MILESTONE_CANCELLED = 'milestone_cancelled', _('Milestone Cancelled')
    
    # Order events
    ORDER_CREATED = 'order_created', _('Order Created')
    ORDER_CONFIRMED = 'order_confirmed', _('Order Confirmed')
    ORDER_PAID = 'order_paid', _('Order Paid')
    ORDER_SHIPPED = 'order_shipped', _('Order Shipped')
    ORDER_DELIVERED = 'order_delivered', _('Order Delivered')
    ORDER_CANCELLED = 'order_cancelled', _('Order Cancelled')
    
    # Task events
    TASK_CREATED = 'task_created', _('Task Created')
    TASK_ASSIGNED = 'task_assigned', _('Task Assigned')
    TASK_STARTED = 'task_started', _('Task Started')
    TASK_COMPLETED = 'task_completed', _('Task Completed')
    TASK_COMMENTED = 'task_commented', _('Task Commented')
    
    # User events
    USER_JOINED = 'user_joined', _('User Joined')
    USER_UPDATED = 'user_updated', _('User Updated')
    USER_COMMENTED = 'user_commented', _('User Commented')
    
    # System events
    SYSTEM_MAINTENANCE = 'system_maintenance', _('System Maintenance')
    SYSTEM_UPDATE = 'system_update', _('System Update')
    SYSTEM_ALERT = 'system_alert', _('System Alert')
    
    # Product events
    PRODUCT_CREATED = 'product_created', _('Product Created')
    PRODUCT_UPDATED = 'product_updated', _('Product Updated')
    PRODUCT_PRICE_CHANGED = 'product_price_changed', _('Price Changed')
    PRODUCT_STOCK_LOW = 'product_stock_low', _('Stock Low')


class MilestoneStatus(ChoiceEnum):
    """Status states for milestones."""
    PENDING = 'pending', _('Pending')
    PLANNED = 'planned', _('Planned')
    IN_PROGRESS = 'in_progress', _('In Progress')
    COMPLETED = 'completed', _('Completed')
    DELAYED = 'delayed', _('Delayed')
    CANCELLED = 'cancelled', _('Cancelled')
    ON_HOLD = 'on_hold', _('On Hold')


class MilestonePriority(ChoiceEnum):
    """Priority levels for milestones."""
    LOW = 'low', _('Low')
    MEDIUM = 'medium', _('Medium')
    HIGH = 'high', _('High')
    CRITICAL = 'critical', _('Critical')


class SubscriptionType(ChoiceEnum):
    """Types of stream subscriptions."""
    FOLLOW = 'follow', _('Follow')
    WATCH = 'watch', _('Watch')
    NOTIFY = 'notify', _('Notify Only')
    MUTE = 'mute', _('Muted')


class EventImportance(ChoiceEnum):
    """Importance levels for events."""
    LOW = 'low', _('Low')
    NORMAL = 'normal', _('Normal')
    HIGH = 'high', _('High')
    CRITICAL = 'critical', _('Critical')