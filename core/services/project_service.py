"""
Project Service Module

Handles business logic for project management including
workflow operations and task management.
"""

from typing import Dict, Any, Optional

from django.utils import timezone

from .base import BaseService, ServiceResult, ValidationError
from core.enums import ProjectStatus, TaskStatus, TicketStatus
from core.state_machine import ProjectWorkflow, WorkflowMixin


class ProjectService(BaseService):
    """
    Service for managing projects and their lifecycle.
    """
    
    from project.models import Project
    model_class = Project
    workflow_class = ProjectWorkflow
    
    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Validate project data."""
        errors = {}
        
        if not data.get('societe_id'):
            errors['societe'] = "Societe is required"
        
        if errors:
            raise ValidationError("Validation failed", errors)
        
        return data
    
    def perform_create(self, validated_data: Dict[str, Any]) -> Any:
        """Create project."""
        # Handle societe
        societe_id = validated_data.pop('societe_id', None)
        if societe_id:
            from core.profile.models import Societe
            validated_data['societe'] = Societe.objects.get(id=societe_id)
        
        instance = super().perform_create(validated_data)
        return instance
    
    def perform_update(
        self,
        instance: Any,
        validated_data: Dict[str, Any]
    ) -> Any:
        """Update project."""
        # Handle societe
        societe_id = validated_data.pop('societe_id', None)
        if societe_id:
            from core.profile.models import Societe
            validated_data['societe'] = Societe.objects.get(id=societe_id)
        
        return super().perform_update(instance, validated_data)
    
    def start_pre_construction(self, project_id: int) -> ServiceResult:
        """Start pre-construction phase."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        return self.execute_workflow_trigger(
            project,
            'start_pre_construction'
        )
    
    def start_construction(self, project_id: int) -> ServiceResult:
        """Start construction phase."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        return self.execute_workflow_trigger(
            project,
            'start_construction'
        )
    
    def complete_construction(self, project_id: int) -> ServiceResult:
        """Mark construction as complete."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        return self.execute_workflow_trigger(
            project,
            'complete_construction'
        )
    
    def start_sales(self, project_id: int) -> ServiceResult:
        """Start sales phase."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        return self.execute_workflow_trigger(project, 'start_sales')
    
    def sell_out(self, project_id: int) -> ServiceResult:
        """Mark project as sold out."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        return self.execute_workflow_trigger(project, 'sell_out')
    
    def hold(self, project_id: int, reason: str = "") -> ServiceResult:
        """Put project on hold."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        if reason and hasattr(project, 'hold_reason'):
            project.hold_reason = reason
            project.save(update_fields=['hold_reason'])
        
        return self.execute_workflow_trigger(project, 'hold')
    
    def resume(self, project_id: int) -> ServiceResult:
        """Resume a project on hold."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        # Determine which resume trigger to use based on previous state
        if hasattr(project, 'previous_status'):
            trigger_map = {
                ProjectStatus.PLANNING.value: 'resume',
                ProjectStatus.PRE_CONSTRUCTION.value: (
                    'resume_pre_construction'
                ),
                ProjectStatus.UNDER_CONSTRUCTION.value: (
                    'resume_construction'
                ),
            }
            trigger = trigger_map.get(project.previous_status, 'resume')
        else:
            trigger = 'resume'
        
        return self.execute_workflow_trigger(project, trigger)
    
    def cancel(self, project_id: int, reason: str = "") -> ServiceResult:
        """Cancel a project."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        if reason and hasattr(project, 'cancellation_reason'):
            project.cancellation_reason = reason
            project.save(update_fields=['cancellation_reason'])
        
        return self.execute_workflow_trigger(project, 'cancel')
    
    def get_project_summary(self, project_id: int) -> ServiceResult:
        """Get detailed project summary."""
        project = self.get_by_id(project_id)
        if not project:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        summary = {
            'id': project.id,
            'code': project.code,
            'status': project.status,
            'societe': {
                'id': project.societe_id,
                'name': str(project.societe)
            },
            'category': project.category.name if project.category else None,
            'location': {
                'lat': project.lat,
                'lon': project.lon
            },
            'active': project.active,
            'created': project.created,
            'images_count': (
                project.images.count()
                if hasattr(project, 'images')
                else 0
            ),
            'available_transitions': []
        }
        
        if isinstance(project, WorkflowMixin):
            summary['available_transitions'] = project.get_available_triggers()
        
        return ServiceResult.ok(summary)
    
    def list_by_status(self, status: ProjectStatus) -> ServiceResult:
        """List projects by status."""
        projects = self.get_queryset().filter(status=status.value)
        return ServiceResult.ok(list(projects))
    
    def list_active(self) -> ServiceResult:
        """List all active projects."""
        projects = self.get_queryset().filter(active=True).exclude(
            status__in=[
                ProjectStatus.CANCELLED.value,
                ProjectStatus.SOLD_OUT.value
            ]
        )
        return ServiceResult.ok(list(projects))


class TaskService(BaseService):
    """
    Service for managing tasks within projects.
    """
    
    from project.models import Task
    
    def create_task(
        self,
        project_id: int,
        task_data: Dict[str, Any]
    ) -> ServiceResult:
        """Create a task for a project."""
        from project.models import Project
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        try:
            task_data['project'] = project
            if self.user:
                task_data['created_by'] = self.user
            
            task = self.model_class.objects.create(**task_data)
            return ServiceResult.ok(task, "Task created successfully")
            
        except Exception as e:
            return ServiceResult.fail(f"Task creation failed: {str(e)}")
    
    def complete_task(self, task_id: int) -> ServiceResult:
        """Mark a task as completed."""
        task = self.get_by_id(task_id)
        if not task:
            return ServiceResult.fail(f"Task {task_id} not found")
        
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = timezone.now()
        task.save()
        
        return ServiceResult.ok(task, "Task marked as completed")


class TicketService(BaseService):
    """
    Service for managing tickets/issues within projects.
    """
    
    from project.models import Ticket
    
    def create_ticket(
        self,
        project_id: int,
        ticket_data: Dict[str, Any]
    ) -> ServiceResult:
        """Create a ticket for a project."""
        from project.models import Project
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return ServiceResult.fail(f"Project {project_id} not found")
        
        try:
            ticket_data['project'] = project
            if self.user:
                ticket_data['created_by'] = self.user
            
            ticket = self.model_class.objects.create(**ticket_data)
            return ServiceResult.ok(ticket, "Ticket created successfully")
            
        except Exception as e:
            return ServiceResult.fail(f"Ticket creation failed: {str(e)}")
    
    def resolve_ticket(
        self,
        ticket_id: int,
        resolution: str = ""
    ) -> ServiceResult:
        """Mark a ticket as resolved."""
        ticket = self.get_by_id(ticket_id)
        if not ticket:
            return ServiceResult.fail(f"Ticket {ticket_id} not found")
        
        ticket.status = TicketStatus.RESOLVED.value
        if resolution:
            ticket.resolution = resolution
        ticket.save()
        
        return ServiceResult.ok(ticket, "Ticket resolved")
