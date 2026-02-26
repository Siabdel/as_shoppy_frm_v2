from django.utils import timezone
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from polymorphic.admin import PolymorphicInlineSupportMixin

from project import models as proj_models
from product import admin as pro_admin
from core.utils import get_product_model

# Load default product
Product_model = get_product_model()


class ProductInline(pro_admin.ProductImageAdminMixin, admin.TabularInline):
    model = Product_model
    prepopulated_fields = {'slug': ('name',)}
    fields = ('name', 'slug', 'default_image', 'price', 'stock')
    extra = 1


class ProjectImagesInline(admin.TabularInline):
    model = proj_models.ProjectImage
    readonly_fields = ('thumbnail_path', 'large_path')
    fields = ('title', 'image')
    extra = 0


class TaskInline(admin.TabularInline):
    model = proj_models.Task
    fields = ('title', 'status', 'priority', 'assigned_to', 'due_date')
    extra = 0
    show_change_link = True


class TicketInline(admin.TabularInline):
    model = proj_models.Ticket
    fields = ('title', 'status', 'priority', 'assigned_to', 'due_date')
    extra = 0
    show_change_link = True


@admin.register(proj_models.Project)
class ProjectAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    inlines = [ProjectImagesInline, ProductInline, TaskInline, TicketInline]
    list_display = [
        'slug', 'code', 'name', 'societe', 
        'author', 'manager', 'start_date', 
        'visibilite', 'status', 'active'
    ]
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['status', 'visibilite', 'active', 'start_date', 'created_at']
    list_editable = ['status', 'active']
    search_fields = ['code', 'name', 'slug', 'description']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (
            "Required Information", {
                "description": "Enter the Project information",
                "fields": (
                    ('societe', 'category'),
                    ('name', 'slug'), 
                    'description',
                ),
            },
        ),
        (
            "Management", {
                "fields": (
                    ('author', 'manager'),
                    ('status', 'visibilite', 'active'),
                ),
            },
        ),
        (
            "Dates", {
                "fields": (
                    ('start_date', 'end_date', 'due_date'),
                    'closed_date',
                ),
            },
        ),
        (
            "Location", {
                "classes": ("collapse",),
                "fields": (
                    'lon',
                    'lat',
                ),
            },
        ),
        (
            "Additional Information", {
                "classes": ("collapse",),
                "fields": (
                    'default_image',
                    'comment',
                ),
            },
        ),
    )
    
    def get_changeform_initial_data(self, request):
        return {
            'author': request.user.id,
            'manager': request.user.id,
            'start_date': timezone.now(),
        }


@admin.register(proj_models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'status', 'priority', 
        'task_type', 'assigned_to', 'due_date', 'created_at'
    ]
    list_filter = ['status', 'priority', 'task_type', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'priority']
    
    fieldsets = (
        (
            "Task Information", {
                "fields": (
                    'title',
                    'description',
                    'project',
                ),
            },
        ),
        (
            "Assignment", {
                "fields": (
                    ('created_by', 'assigned_to'),
                ),
            },
        ),
        (
            "Status & Priority", {
                "fields": (
                    ('status', 'priority', 'task_type'),
                ),
            },
        ),
        (
            "Dates", {
                "fields": (
                    ('due_date', 'completed_at'),
                ),
            },
        ),
    )
    
    def get_changeform_initial_data(self, request):
        return {
            'created_by': request.user.id,
        }


@admin.register(proj_models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'project', 'status', 'priority', 
        'ticket_type', 'assigned_to', 'due_date', 'created_at'
    ]
    list_filter = ['status', 'priority', 'ticket_type', 'created_at']
    search_fields = ['title', 'description', 'resolution']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'priority']
    
    fieldsets = (
        (
            "Ticket Information", {
                "fields": (
                    'title',
                    'description',
                    'project',
                ),
            },
        ),
        (
            "Assignment", {
                "fields": (
                    ('created_by', 'assigned_to'),
                ),
            },
        ),
        (
            "Status & Priority", {
                "fields": (
                    ('status', 'priority', 'ticket_type'),
                ),
            },
        ),
        (
            "Resolution", {
                "classes": ("collapse",),
                "fields": (
                    'resolution',
                    'resolved_at',
                ),
            },
        ),
        (
            "Dates", {
                "fields": (
                    ('due_date',),
                ),
            },
        ),
    )
    
    def get_changeform_initial_data(self, request):
        return {
            'created_by': request.user.id,
        }


@admin.register(proj_models.ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'project__name']


@admin.register(proj_models.Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ['tiers_id', 'tiers_name', 'tiers_type', 'content_object']
    list_filter = ['tiers_type']
    search_fields = ['tiers_id', 'tiers_name']
