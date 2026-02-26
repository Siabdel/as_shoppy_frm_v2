"""
Base Service Module

Provides abstract base classes and utilities for the service layer.
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from django.db import transaction


class ServiceError(Exception):
    """Base exception for service layer errors."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


class ValidationError(ServiceError):
    """Exception raised when service validation fails."""
    pass


class NotFoundError(ServiceError):
    """Exception raised when an entity is not found."""
    pass


T = TypeVar('T')


class ServiceResult(Generic[T]):
    """
    Result wrapper for service operations.
    
    Provides a consistent interface for handling success/failure scenarios.
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[T] = None,
        message: str = "",
        errors: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or {}
    
    @classmethod
    def ok(cls, data: T, message: str = "") -> 'ServiceResult[T]':
        """Create a successful result."""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def fail(
        cls,
        message: str,
        errors: Optional[Dict[str, Any]] = None
    ) -> 'ServiceResult[T]':
        """Create a failed result."""
        return cls(success=False, message=message, errors=errors)
    
    @property
    def is_ok(self) -> bool:
        return self.success
    
    @property
    def is_fail(self) -> bool:
        return not self.success


class BaseService:
    """
    Abstract base class for all services.
    
    Services encapsulate business logic and orchestrate operations
    across multiple models. They provide:
    - Transaction management
    - Validation
    - Workflow integration
    - Event triggering
    """
    
    # Model class managed by this service
    model_class = None
    
    # Workflow class for state management
    workflow_class = None
    
    def __init__(self, user=None, context: Optional[Dict[str, Any]] = None):
        """
        Initialize service.
        
        Args:
            user: The user executing the operation
            context: Additional context data
        """
        self.user = user
        self.context = context or {}
    
    def get_queryset(self):
        """Get base queryset for the service's model."""
        if self.model_class is None:
            raise NotImplementedError("model_class must be defined")
        return self.model_class.objects.all()
    
    def get_by_id(self, pk: int) -> Optional[Any]:
        """Get entity by primary key."""
        try:
            return self.get_queryset().get(pk=pk)
        except self.model_class.DoesNotExist:
            return None
    
    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Validate input data.
        
        Args:
            data: Input data to validate
            instance: Existing instance if updating
            
        Returns:
            Validated and cleaned data
            
        Raises:
            ValidationError: If validation fails
        """
        return data
    
    def create(self, data: Dict[str, Any]) -> ServiceResult:
        """
        Create a new entity.
        
        Args:
            data: Entity data
            
        Returns:
            ServiceResult with created entity
        """
        try:
            validated_data = self.validate(data)
            
            with transaction.atomic():
                instance = self.perform_create(validated_data)
                self.after_create(instance, validated_data)
                
            return ServiceResult.ok(instance, "Created successfully")
            
        except ValidationError as e:
            return ServiceResult.fail(str(e), e.errors)
        except Exception as e:
            return ServiceResult.fail(f"Creation failed: {str(e)}")
    
    def update(self, pk: int, data: Dict[str, Any]) -> ServiceResult:
        """
        Update an existing entity.
        
        Args:
            pk: Entity primary key
            data: Updated data
            
        Returns:
            ServiceResult with updated entity
        """
        try:
            instance = self.get_by_id(pk)
            if not instance:
                return ServiceResult.fail(f"Entity with id {pk} not found")
            
            validated_data = self.validate(data, instance)
            
            with transaction.atomic():
                instance = self.perform_update(instance, validated_data)
                self.after_update(instance, validated_data)
                
            return ServiceResult.ok(instance, "Updated successfully")
            
        except ValidationError as e:
            return ServiceResult.fail(str(e), e.errors)
        except Exception as e:
            return ServiceResult.fail(f"Update failed: {str(e)}")
    
    def delete(self, pk: int) -> ServiceResult:
        """
        Delete an entity.
        
        Args:
            pk: Entity primary key
            
        Returns:
            ServiceResult indicating success/failure
        """
        try:
            instance = self.get_by_id(pk)
            if not instance:
                return ServiceResult.fail(f"Entity with id {pk} not found")
            
            with transaction.atomic():
                self.before_delete(instance)
                instance.delete()
                
            return ServiceResult.ok(None, "Deleted successfully")
            
        except Exception as e:
            return ServiceResult.fail(f"Deletion failed: {str(e)}")
    
    def perform_create(self, validated_data: Dict[str, Any]) -> Any:
        """Perform the actual creation. Override in subclasses."""
        return self.model_class.objects.create(**validated_data)
    
    def perform_update(
        self,
        instance: Any,
        validated_data: Dict[str, Any]
    ) -> Any:
        """Perform the actual update. Override in subclasses."""
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
    
    def after_create(self, instance: Any, validated_data: Dict[str, Any]):
        """Hook executed after successful creation."""
        pass
    
    def after_update(self, instance: Any, validated_data: Dict[str, Any]):
        """Hook executed after successful update."""
        pass
    
    def before_delete(self, instance: Any):
        """Hook executed before deletion."""
        pass
    
    def execute_workflow_trigger(
        self,
        instance: Any,
        trigger_name: str,
        *args,
        **kwargs
    ) -> ServiceResult:
        """
        Execute a workflow trigger on an instance.
        
        Args:
            instance: Entity instance
            trigger_name: Name of the trigger to execute
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            ServiceResult indicating success/failure
        """
        from core.state_machine import WorkflowMixin
        
        if not isinstance(instance, WorkflowMixin):
            msg = (
                f"Instance of type {type(instance).__name__} "
                f"does not support workflows"
            )
            return ServiceResult.fail(msg)

        try:
            instance.execute_trigger(trigger_name, *args, **kwargs)
            instance.save()
            msg = f"Trigger '{trigger_name}' executed"
            return ServiceResult.ok(instance, msg)
        except Exception as e:
            return ServiceResult.fail(f"Trigger execution failed: {str(e)}")


class BulkServiceMixin:
    """Mixin for services that support bulk operations."""
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> ServiceResult:
        """Create multiple entities in a single transaction."""
        created = []
        errors = []
        
        with transaction.atomic():
            for idx, data in enumerate(items):
                try:
                    validated = self.validate(data)
                    instance = self.perform_create(validated)
                    created.append(instance)
                except Exception as e:
                    errors.append({"index": idx, "error": str(e)})
        
        if errors:
            return ServiceResult.fail(
                f"Bulk create partially failed: {len(errors)} errors",
                {"created": len(created), "errors": errors}
            )
        
        return ServiceResult.ok(created, f"Created {len(created)} items")
    
    def bulk_update(
        self,
        updates: List[Dict[str, Any]]
    ) -> ServiceResult:
        """
        Update multiple entities.
        
        Args:
            updates: List of dicts with 'id' key and update data
        """
        updated = []
        errors = []
        
        with transaction.atomic():
            for idx, data in enumerate(updates):
                pk = data.pop('id', None)
                if not pk:
                    errors.append({"index": idx, "error": "Missing 'id' key"})
                    continue
                
                result = self.update(pk, data)
                if result.is_ok:
                    updated.append(result.data)
                else:
                    errors.append({"index": idx, "error": result.message})
        
        if errors:
            return ServiceResult.fail(
                f"Bulk update partially failed: {len(errors)} errors",
                {"updated": len(updated), "errors": errors}
            )
        
        return ServiceResult.ok(updated, f"Updated {len(updated)} items")


class AuditedServiceMixin:
    """Mixin for services that track user actions."""
    
    def after_create(self, instance: Any, validated_data: Dict[str, Any]):
        """Record creation audit."""
        super().after_create(instance, validated_data)
        if hasattr(instance, 'created_by') and self.user:
            instance.created_by = self.user
            instance.save(update_fields=['created_by'])
    
    def after_update(self, instance: Any, validated_data: Dict[str, Any]):
        """Record update audit."""
        super().after_update(instance, validated_data)
        if hasattr(instance, 'updated_by') and self.user:
            instance.updated_by = self.user
            instance.save(update_fields=['updated_by'])