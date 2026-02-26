# Streams & Milestones System

A comprehensive activity stream and milestone tracking system for the marketplace application.

## Overview

The Streams & Milestones system provides:

- **Activity Streams**: Real-time tracking of events across projects, orders, and user activities
- **Milestones**: Project milestone management with progress tracking and dependencies
- **Subscriptions**: User subscription system for following streams and receiving notifications
- **Event Aggregation**: Centralized event collection with filtering and importance levels

## Models

### Stream
A stream represents a sequence of events related to a specific object (project, order, user, etc.).

```python
from core.streams.models import Stream
from core.streams.enums import StreamType

# Create a stream for a project
stream = Stream.objects.create(
    name="Project Alpha Stream",
    stream_type=StreamType.PROJECT,
    content_object=project,
    is_active=True
)
```

**Key Features:**
- Generic relations to any model (projects, orders, products)
- Automatic slug generation
- Event count caching
- Subscriber count tracking

### StreamEvent
Individual events in a stream. Events are immutable records of actions.

```python
from core.streams.models import StreamEvent
from core.streams.enums import EventType, EventImportance

# Add an event to a stream
event = stream.add_event(
    event_type=EventType.PROJECT_UPDATED,
    description="Project scope was updated",
    actor=request.user,
    importance=EventImportance.HIGH,
    metadata={'changed_fields': ['scope', 'budget']}
)
```

**Event Types:**
- Project events: `PROJECT_CREATED`, `PROJECT_UPDATED`, `PROJECT_STATUS_CHANGED`, etc.
- Milestone events: `MILESTONE_CREATED`, `MILESTONE_STARTED`, `MILESTONE_COMPLETED`, etc.
- Order events: `ORDER_CREATED`, `ORDER_PAID`, `ORDER_SHIPPED`, etc.
- Task events: `TASK_CREATED`, `TASK_ASSIGNED`, `TASK_COMPLETED`, etc.

### Milestone
Project milestones with progress tracking and dependencies.

```python
from core.streams.models import Milestone
from core.streams.enums import MilestoneStatus, MilestonePriority

# Create a milestone
milestone = Milestone.objects.create(
    name="Foundation Phase",
    project=project,
    status=MilestoneStatus.PLANNED,
    priority=MilestonePriority.HIGH,
    planned_start_date=date(2026, 3, 1),
    planned_end_date=date(2026, 4, 15),
    assigned_to=user,
    budget=Decimal('50000.00')
)

# Start the milestone
milestone.start()

# Update progress
milestone.update_progress(50)

# Complete the milestone
milestone.complete()
```

**Key Features:**
- Dependency management (milestones can depend on others)
- Progress tracking (0-100%)
- Financial tracking (budget vs actual cost)
- Automatic stream creation
- Overdue detection

### StreamSubscription
User subscriptions to streams for notifications.

```python
from core.streams.models import StreamSubscription
from core.streams.enums import SubscriptionType

# Subscribe to a stream
subscription = StreamSubscription.objects.create(
    user=user,
    stream=stream,
    subscription_type=SubscriptionType.FOLLOW,
    notify_email=True,
    notify_push=False,
    min_importance=EventImportance.NORMAL
)

# Mark as read
subscription.mark_as_read()
```

### MilestoneComment
Comments on milestones for team communication.

```python
# Add a comment
comment = MilestoneComment.objects.create(
    milestone=milestone,
    author=user,
    content="Making good progress on this phase"
)

# Reply to a comment
reply = MilestoneComment.objects.create(
    milestone=milestone,
    author=other_user,
    content="Great! Let me know if you need help.",
    parent=comment
)
```

## Services

### StreamService
Business logic for stream operations.

```python
from core.streams.services import StreamService

service = StreamService(user=request.user)

# Get or create stream for any object
stream = service.get_or_create_for_object(
    obj=project,
    stream_type=StreamType.PROJECT
)

# Get user's personalized feed
result = service.get_user_stream_feed(user, limit=50)
if result.success:
    events = result.data

# Search events
result = service.search_events(query="foundation", limit=20)
```

### MilestoneService
Business logic for milestone operations.

```python
from core.streams.services import MilestoneService

service = MilestoneService(user=request.user)

# Create a milestone with associated stream
result = service.create({
    'name': 'Roof Construction',
    'project_id': project.id,
    'priority': MilestonePriority.HIGH,
    'planned_end_date': date(2026, 6, 1),
    'assigned_to': user,
    'created_by': request.user
})

# Start milestone
result = service.start_milestone(milestone_id)

# Get project timeline
result = service.get_project_timeline(project.id)
if result.success:
    timeline = result.data
    # Contains: milestones, statistics, progress

# Get critical path
result = service.get_critical_path(project.id)
```

### SubscriptionService
Business logic for subscription management.

```python
from core.streams.services import SubscriptionService

service = SubscriptionService(user=request.user)

# Subscribe to stream
result = service.subscribe(
    user=user,
    stream_id=stream.id,
    subscription_type=SubscriptionType.FOLLOW
)

# Get user dashboard
result = service.get_user_dashboard(user)
if result.success:
    dashboard = result.data
    # Contains: subscription_count, total_unread, recent_events,
    #           assigned_milestones, subscriptions
```

## API Endpoints

### Streams

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/streams/` | List streams |
| POST | `/api/streams/` | Create stream |
| GET | `/api/streams/{slug}/` | Get stream details |
| POST | `/api/streams/{slug}/add_event/` | Add event to stream |
| GET | `/api/streams/{slug}/events/` | Get stream events |
| POST | `/api/streams/{slug}/subscribe/` | Subscribe to stream |
| POST | `/api/streams/{slug}/unsubscribe/` | Unsubscribe from stream |
| POST | `/api/streams/{slug}/mark_read/` | Mark stream as read |
| GET | `/api/streams/my_feed/` | Get personalized feed |
| GET | `/api/streams/search/?q={query}` | Search events |

### Milestones

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/milestones/` | List milestones |
| POST | `/api/milestones/` | Create milestone |
| GET | `/api/milestones/{id}/` | Get milestone details |
| PUT/PATCH | `/api/milestones/{id}/` | Update milestone |
| DELETE | `/api/milestones/{id}/` | Delete milestone |
| POST | `/api/milestones/{id}/start/` | Start milestone |
| POST | `/api/milestones/{id}/complete/` | Complete milestone |
| POST | `/api/milestones/{id}/update_progress/` | Update progress |
| GET | `/api/milestones/{id}/timeline/` | Get project timeline |
| GET | `/api/milestones/{id}/comments/` | Get comments |
| POST | `/api/milestones/{id}/add_comment/` | Add comment |
| GET | `/api/milestones/my_milestones/` | Get assigned milestones |
| GET | `/api/milestones/dashboard/` | Get user dashboard |

### Subscriptions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subscriptions/` | List my subscriptions |
| GET | `/api/subscriptions/{id}/` | Get subscription details |
| GET | `/api/subscriptions/unread_counts/` | Get unread counts |
| POST | `/api/subscriptions/{id}/mark_read/` | Mark as read |
| GET | `/api/subscriptions/dashboard/` | Get dashboard |

## Signals

The system includes automatic signal handlers for creating stream events:

- **Project created/updated**: Automatically creates `Stream` and adds events
- **Order created**: Automatically creates stream for orders

## Admin Interface

All models are registered in Django admin with:

- **StreamAdmin**: List filters for type/status, search by name/description
- **StreamEventAdmin**: Importance badges, event type filters, colored indicators
- **MilestoneAdmin**: Status badges, progress bars, overdue indicators
- **StreamSubscriptionAdmin**: Notification preferences, read tracking
- **MilestoneCommentAdmin**: Threading support, edit tracking

## Usage Examples

### Creating a Project with Milestones

```python
from project.models import Project
from core.streams.services import MilestoneService, StreamService
from core.streams.enums import MilestonePriority
from datetime import date, timedelta

# Create project
project = Project.objects.create(
    name="Commercial Building A",
    societe=societe,
    status=ProjectStatus.PLANNING
)

# Create milestones
service = MilestoneService()
milestones_data = [
    {
        'name': 'Site Preparation',
        'project_id': project.id,
        'priority': MilestonePriority.HIGH,
        'planned_start_date': date(2026, 3, 1),
        'planned_end_date': date(2026, 3, 15),
    },
    {
        'name': 'Foundation',
        'project_id': project.id,
        'priority': MilestonePriority.HIGH,
        'planned_start_date': date(2026, 3, 16),
        'planned_end_date': date(2026, 4, 30),
    },
    {
        'name': 'Structure',
        'project_id': project.id,
        'priority': MilestonePriority.CRITICAL,
        'planned_start_date': date(2026, 5, 1),
        'planned_end_date': date(2026, 7, 31),
    }
]

# Create milestones (each gets its own stream)
for data in milestones_data:
    service.create(data)

# Set up dependencies
foundation = Milestone.objects.get(name='Foundation', project=project)
structure = Milestone.objects.get(name='Structure', project=project)
structure.dependencies.add(foundation)

# Start first milestone when ready
foundation.start()
```

### Tracking Order Progress

```python
from core.orders.models import Order
from core.streams.services import StreamService
from core.streams.enums import EventType, EventImportance

# Stream is auto-created on order creation
order = Order.objects.create(
    customer=customer,
    # ... other fields
)

# Get or create stream
service = StreamService()
stream = service.get_or_create_for_object(
    order,
    stream_type=StreamType.ORDER,
    name=f"Order #{order.id} Stream"
)

# Add custom events
stream.add_event(
    event_type=EventType.ORDER_CONFIRMED,
    description="Order has been confirmed by customer",
    actor=staff_user,
    importance=EventImportance.HIGH
)

stream.add_event(
    event_type=EventType.ORDER_SHIPPED,
    description=f"Order shipped via {carrier}",
    actor=staff_user,
    importance=EventImportance.NORMAL,
    metadata={
        'tracking_number': tracking_number,
        'carrier': carrier,
        'estimated_delivery': delivery_date.isoformat()
    }
)
```

### User Dashboard

```python
from core.streams.services import SubscriptionService

service = SubscriptionService(user=request.user)

# Get comprehensive dashboard
dashboard = service.get_user_dashboard(request.user)

# Access dashboard data
print(f"Subscriptions: {dashboard['subscription_count']}")
print(f"Unread events: {dashboard['total_unread']}")
print(f"Assigned milestones: {len(dashboard['assigned_milestones'])}")

for event in dashboard['recent_events']:
    print(f"{event['created_at']}: {event['description']}")
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'core.streams',
]
```

Add URLs:

```python
urlpatterns = [
    # ... other urls
    path("api/streams/", include("core.streams.urls")),
]
```

## Database Indexes

The system includes optimized database indexes for:
- Stream lookups by type and active status
- Event queries by stream and creation date
- Milestone queries by project and status
- Subscription lookups by user

## Performance Considerations

- Event counts and subscriber counts are denormalized and cached
- Use `select_related` and `prefetch_related` for API queries
- Consider pagination for large event lists
- Dashboard data can be cached per user

## Future Enhancements

- Real-time WebSocket notifications
- Email notification templates
- Mobile push notification integration
- Advanced analytics and reporting
- Gantt chart visualization for milestones
- Calendar integration