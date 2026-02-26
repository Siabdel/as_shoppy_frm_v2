# Generated Django migration for core.streams app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Initial migration for streams app."""

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '0001_initial'),  # Adjust based on actual project migration
    ]

    operations = [
        # Stream model
        migrations.CreateModel(
            name='Stream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Stream Name')),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('stream_type', models.CharField(choices=[('project', 'Project Stream'), ('order', 'Order Stream'), ('user', 'User Activity Stream'), ('system', 'System Stream'), ('milestone', 'Milestone Stream'), ('product', 'Product Stream')], default='project', max_length=50, verbose_name='Stream Type')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Object ID')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('is_public', models.BooleanField(default=True, verbose_name='Is Public')),
                ('event_count', models.PositiveIntegerField(default=0, verbose_name='Event Count')),
                ('subscriber_count', models.PositiveIntegerField(default=0, verbose_name='Subscriber Count')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('last_event_at', models.DateTimeField(blank=True, null=True, verbose_name='Last Event At')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Content Type')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_streams', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
            ],
            options={
                'verbose_name': 'Stream',
                'verbose_name_plural': 'Streams',
                'ordering': ['-last_event_at', '-created_at'],
            },
        ),
        # StreamEvent model
        migrations.CreateModel(
            name='StreamEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('project_created', 'Project Created'), ('project_updated', 'Project Updated'), ('project_status_changed', 'Status Changed'), ('project_phase_started', 'Phase Started'), ('project_completed', 'Project Completed'), ('milestone_created', 'Milestone Created'), ('milestone_started', 'Milestone Started'), ('milestone_completed', 'Milestone Completed'), ('milestone_delayed', 'Milestone Delayed'), ('milestone_cancelled', 'Milestone Cancelled'), ('order_created', 'Order Created'), ('order_confirmed', 'Order Confirmed'), ('order_paid', 'Order Paid'), ('order_shipped', 'Order Shipped'), ('order_delivered', 'Order Delivered'), ('order_cancelled', 'Order Cancelled'), ('task_created', 'Task Created'), ('task_assigned', 'Task Assigned'), ('task_started', 'Task Started'), ('task_completed', 'Task Completed'), ('task_commented', 'Task Commented'), ('user_joined', 'User Joined'), ('user_updated', 'User Updated'), ('user_commented', 'User Commented'), ('system_maintenance', 'System Maintenance'), ('system_update', 'System Update'), ('system_alert', 'System Alert'), ('product_created', 'Product Created'), ('product_updated', 'Product Updated'), ('product_price_changed', 'Price Changed'), ('product_stock_low', 'Stock Low')], max_length=50, verbose_name='Event Type')),
                ('importance', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')], default='normal', max_length=20, verbose_name='Importance')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description')),
                ('actor_display', models.CharField(blank=True, max_length=255, verbose_name='Actor Display Name')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='Object ID')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadata')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stream_events', to=settings.AUTH_USER_MODEL, verbose_name='Actor')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Content Type')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='streams.stream', verbose_name='Stream')),
            ],
            options={
                'verbose_name': 'Stream Event',
                'verbose_name_plural': 'Stream Events',
                'ordering': ['-created_at'],
            },
        ),
        # Milestone model
        migrations.CreateModel(
            name='Milestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Milestone Name')),
                ('slug', models.SlugField(blank=True, max_length=255, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('planned', 'Planned'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('delayed', 'Delayed'), ('cancelled', 'Cancelled'), ('on_hold', 'On Hold')], default='pending', max_length=20, verbose_name='Status')),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], default='medium', max_length=20, verbose_name='Priority')),
                ('planned_start_date', models.DateField(blank=True, null=True, verbose_name='Planned Start Date')),
                ('planned_end_date', models.DateField(blank=True, null=True, verbose_name='Planned End Date')),
                ('actual_start_date', models.DateField(blank=True, null=True, verbose_name='Actual Start Date')),
                ('actual_end_date', models.DateField(blank=True, null=True, verbose_name='Actual End Date')),
                ('progress_percentage', models.PositiveSmallIntegerField(default=0, verbose_name='Progress %')),
                ('budget', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Budget')),
                ('actual_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Actual Cost')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadata')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completed At')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_milestones', to=settings.AUTH_USER_MODEL, verbose_name='Assigned To')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_milestones', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('dependencies', models.ManyToManyField(blank=True, related_name='dependent_milestones', to='streams.milestone', verbose_name='Dependencies')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='project.project', verbose_name='Project')),
                ('stream', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='milestones', to='streams.stream', verbose_name='Associated Stream')),
            ],
            options={
                'verbose_name': 'Milestone',
                'verbose_name_plural': 'Milestones',
                'ordering': ['planned_end_date', 'priority', 'created_at'],
            },
        ),
        # Add milestone relation to StreamEvent
        migrations.AddField(
            model_name='streamevent',
            name='milestone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='streams.milestone', verbose_name='Related Milestone'),
        ),
        # StreamSubscription model
        migrations.CreateModel(
            name='StreamSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_type', models.CharField(choices=[('follow', 'Follow'), ('watch', 'Watch'), ('notify', 'Notify Only'), ('mute', 'Muted')], default='follow', max_length=20, verbose_name='Subscription Type')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is Active')),
                ('notify_email', models.BooleanField(default=True, verbose_name='Email Notifications')),
                ('notify_push', models.BooleanField(default=False, verbose_name='Push Notifications')),
                ('notify_sms', models.BooleanField(default=False, verbose_name='SMS Notifications')),
                ('min_importance', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')], default='normal', max_length=20, verbose_name='Minimum Importance')),
                ('last_read_at', models.DateTimeField(blank=True, null=True, verbose_name='Last Read At')),
                ('unread_count', models.PositiveIntegerField(default=0, verbose_name='Unread Count')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Subscribed At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='streams.stream', verbose_name='Stream')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stream_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Stream Subscription',
                'verbose_name_plural': 'Stream Subscriptions',
                'ordering': ['-created_at'],
                'unique_together': {('stream', 'user')},
            },
        ),
        # MilestoneComment model
        migrations.CreateModel(
            name='MilestoneComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Content')),
                ('is_edited', models.BooleanField(default=False, verbose_name='Is Edited')),
                ('edited_at', models.DateTimeField(blank=True, null=True, verbose_name='Edited At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestone_comments', to=settings.AUTH_USER_MODEL, verbose_name='Author')),
                ('milestone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='streams.milestone', verbose_name='Milestone')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='streams.milestonecomment', verbose_name='Parent Comment')),
            ],
            options={
                'verbose_name': 'Milestone Comment',
                'verbose_name_plural': 'Milestone Comments',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='stream',
            index=models.Index(fields=['stream_type', 'is_active'], name='streams_str_stream_3d1752_idx'),
        ),
        migrations.AddIndex(
            model_name='stream',
            index=models.Index(fields=['content_type', 'object_id'], name='streams_str_content_1e68a5_idx'),
        ),
        migrations.AddIndex(
            model_name='stream',
            index=models.Index(fields=['slug'], name='streams_str_slug_f3c750_idx'),
        ),
        migrations.AddIndex(
            model_name='stream',
            index=models.Index(fields=['last_event_at'], name='streams_str_last_ev_1f3e6d_idx'),
        ),
        migrations.AddIndex(
            model_name='streamevent',
            index=models.Index(fields=['stream', 'created_at'], name='streams_str_stream__4f6b7c_idx'),
        ),
        migrations.AddIndex(
            model_name='streamevent',
            index=models.Index(fields=['event_type', 'created_at'], name='streams_str_event_t_5a8d9e_idx'),
        ),
        migrations.AddIndex(
            model_name='streamevent',
            index=models.Index(fields=['actor', 'created_at'], name='streams_str_actor_i_d7c4af_idx'),
        ),
        migrations.AddIndex(
            model_name='streamevent',
            index=models.Index(fields=['importance', 'created_at'], name='streams_str_importa_c9e8b1_idx'),
        ),
        migrations.AddIndex(
            model_name='milestone',
            index=models.Index(fields=['project', 'status'], name='streams_mil_project_6b2c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='milestone',
            index=models.Index(fields=['status', 'planned_end_date'], name='streams_mil_status__8e4f5a_idx'),
        ),
        migrations.AddIndex(
            model_name='milestone',
            index=models.Index(fields=['assigned_to', 'status'], name='streams_mil_assigne_c1d2e3_idx'),
        ),
        migrations.AddIndex(
            model_name='milestone',
            index=models.Index(fields=['priority', 'status'], name='streams_mil_priorit_f4a5b6_idx'),
        ),
        migrations.AddIndex(
            model_name='streamsubscription',
            index=models.Index(fields=['user', 'is_active'], name='streams_str_user_id_9c8d7e_idx'),
        ),
        migrations.AddIndex(
            model_name='streamsubscription',
            index=models.Index(fields=['stream', 'is_active'], name='streams_str_stream__2b3c4d_idx'),
        ),
    ]