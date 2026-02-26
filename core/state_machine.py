"""
State Machine Module for Workflow Management

Provides a declarative framework for defining state machines
and managing entity lifecycle workflows.
"""

from typing import List, Set, Callable, Optional, Any, Union
from dataclasses import dataclass
from functools import wraps
from enum import Enum


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class StateMachineError(Exception):
    """Base exception for state machine errors."""
    pass


@dataclass(frozen=True)
class Transition:
    """Represents a valid state transition."""
    source: Union[str, Enum]
    target: Union[str, Enum]
    trigger: Optional[str] = None
    condition: Optional[Callable] = None
    before: Optional[Callable] = None
    after: Optional[Callable] = None
    
    def __post_init__(self):
        object.__setattr__(
            self, '_source_val', 
            self.source.value if isinstance(self.source, Enum) else self.source
        )
        object.__setattr__(
            self, '_target_val',
            self.target.value if isinstance(self.target, Enum) else self.target
        )
    
    @property
    def source_value(self) -> str:
        return self._source_val
    
    @property
    def target_value(self) -> str:
        return self._target_val


class StateMachineMeta(type):
    """Metaclass for building state machine classes."""
    
    def __new__(mcs, name, bases, namespace):
        # Collect transitions from class definition
        transitions = []
        states = set()
        
        for attr_name, attr_value in list(namespace.items()):
            if isinstance(attr_value, Transition):
                transitions.append(attr_value)
                states.add(attr_value.source_value)
                states.add(attr_value.target_value)
        
        namespace['_transitions'] = transitions
        namespace['_states'] = states
        
        return super().__new__(mcs, name, bases, namespace)


class StateMachine(metaclass=StateMachineMeta):
    """
    Base state machine for managing entity workflows.
    
    Usage:
        class QuoteWorkflow(StateMachine):
            draft_to_sent = Transition(
                source=QuoteStatus.DRAFT,
                target=QuoteStatus.SENT,
                trigger='send'
            )
            sent_to_accepted = Transition(
                source=QuoteStatus.SENT,
                target=QuoteStatus.ACCEPTED,
                trigger='accept'
            )
    """
    
    _transitions: List[Transition] = []
    _states: Set[str] = set()
    
    def __init__(self, instance: Any, state_field: str = 'status'):
        self.instance = instance
        self.state_field = state_field
    
    @property
    def current_state(self) -> str:
        """Get the current state value."""
        state = getattr(self.instance, self.state_field)
        return state.value if isinstance(state, Enum) else state
    
    @property
    def available_transitions(self) -> List[Transition]:
        """Get all valid transitions from current state."""
        current = self.current_state
        return [t for t in self._transitions if t.source_value == current]
    
    @property
    def available_triggers(self) -> List[str]:
        """Get all available trigger names from current state."""
        return [t.trigger for t in self.available_transitions if t.trigger]
    
    def can_transition(self, target: Union[str, Enum]) -> bool:
        """Check if transition to target state is valid."""
        target_val = target.value if isinstance(target, Enum) else target
        return any(
            t.target_value == target_val
            for t in self.available_transitions
        )
    
    def can_trigger(self, trigger_name: str) -> bool:
        """Check if trigger is valid from current state."""
        return any(
            t.trigger == trigger_name for t in self.available_transitions
        )
    
    def transition_to(
        self, 
        target: Union[str, Enum], 
        *args, 
        **kwargs
    ) -> bool:
        """
        Attempt to transition to target state.
        
        Args:
            target: The target state value or enum
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            True if transition succeeded
            
        Raises:
            TransitionError: If transition is invalid
        """
        target_val = target.value if isinstance(target, Enum) else target
        
        # Find matching transition
        transition = None
        for t in self._transitions:
            if t.source_value == self.current_state:
                if t.target_value == target_val:
                    transition = t
                    break
        
        if not transition:
            raise TransitionError(
                f"Cannot transition from '{self.current_state}' "
                f"to '{target_val}'"
            )
        
        return self._execute_transition(transition, *args, **kwargs)
    
    def trigger(self, trigger_name: str, *args, **kwargs) -> bool:
        """
        Execute a transition by trigger name.
        
        Args:
            trigger_name: Name of the trigger to execute
            *args: Positional arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
            
        Returns:
            True if transition succeeded
            
        Raises:
            TransitionError: If trigger is invalid
        """
        transition = None
        for t in self._transitions:
            if t.source_value == self.current_state:
                if t.trigger == trigger_name:
                    transition = t
                    break
        
        if not transition:
            raise TransitionError(
                f"Trigger '{trigger_name}' not valid from state "
                f"'{self.current_state}'"
            )
        
        return self._execute_transition(transition, *args, **kwargs)
    
    def _execute_transition(
        self, transition: Transition, *args, **kwargs
    ) -> bool:
        """Execute a transition with all callbacks."""
        # Check condition
        if transition.condition and not transition.condition(
            self.instance, *args, **kwargs
        ):
            raise TransitionError(
                f"Transition condition failed for '{transition.trigger}'"
            )
        
        # Execute before callback
        if transition.before:
            transition.before(self.instance, *args, **kwargs)
        
        # Perform state change
        target_value = transition.target
        if isinstance(transition.target, Enum):
            target_value = transition.target.value
        
        setattr(self.instance, self.state_field, target_value)
        
        # Execute after callback
        if transition.after:
            transition.after(self.instance, *args, **kwargs)
        
        return True
    
    @classmethod
    def get_all_states(cls) -> Set[str]:
        """Get all states defined in this state machine."""
        return cls._states.copy()
    
    @classmethod
    def get_transitions_from(cls, state: Union[str, Enum]) -> List[Transition]:
        """Get all transitions from a specific state."""
        state_val = state.value if isinstance(state, Enum) else state
        return [t for t in cls._transitions if t.source_value == state_val]
    
    @classmethod
    def get_transitions_to(cls, state: Union[str, Enum]) -> List[Transition]:
        """Get all transitions to a specific state."""
        state_val = state.value if isinstance(state, Enum) else state
        return [t for t in cls._transitions if t.target_value == state_val]


# =============================================================================
# Decorators for defining state machine methods
# =============================================================================

def transition(
    source: Union[str, Enum, List[Union[str, Enum]]],
    target: Union[str, Enum],
    conditions: Optional[List[Callable]] = None,
    before: Optional[List[Callable]] = None,
    after: Optional[List[Callable]] = None
):
    """
    Decorator for defining state machine transitions on model methods.
    
    Usage:
        class Quote(models.Model):
            status = models.CharField(max_length=50)
            
            @transition(source=QuoteStatus.DRAFT, target=QuoteStatus.SENT)
            def send(self, user):
                # Transition logic here
                pass
    """
    def decorator(func):
        func._is_transition = True
        func._transition_source = source
        func._transition_target = target
        func._transition_conditions = conditions or []
        func._transition_before = before or []
        func._transition_after = after or []
        
        @wraps(func)
        def wrapper(instance, *args, **kwargs):
            # Get current state
            state_field = getattr(instance, '_state_field', 'status')
            current_state = getattr(instance, state_field)
            if isinstance(current_state, Enum):
                current_val = current_state.value
            else:
                current_val = current_state
            
            # Validate source state
            sources = source if isinstance(source, list) else [source]
            valid_sources = [
                s.value if isinstance(s, Enum) else s for s in sources
            ]
            
            if current_val not in valid_sources:
                raise TransitionError(
                    f"Cannot execute '{func.__name__}' from state "
                    f"'{current_val}'"
                )
            
            # Check conditions
            for condition in func._transition_conditions:
                if not condition(instance, *args, **kwargs):
                    raise TransitionError(
                        f"Condition failed for transition '{func.__name__}'"
                    )
            
            # Execute before hooks
            for hook in func._transition_before:
                hook(instance, *args, **kwargs)
            
            # Execute the transition method
            result = func(instance, *args, **kwargs)
            
            # Update state
            target_val = target.value if isinstance(target, Enum) else target
            setattr(instance, state_field, target_val)
            
            # Execute after hooks
            for hook in func._transition_after:
                hook(instance, *args, **kwargs)
            
            return result
        
        return wrapper
    return decorator


def on_enter(state: Union[str, Enum]):
    """Decorator for methods to execute when entering a state."""
    def decorator(func):
        if isinstance(state, Enum):
            func._on_enter_state = state.value
        else:
            func._on_enter_state = state
        return func
    return decorator


def on_exit(state: Union[str, Enum]):
    """Decorator for methods to execute when exiting a state."""
    def decorator(func):
        if isinstance(state, Enum):
            func._on_exit_state = state.value
        else:
            func._on_exit_state = state
        return func
    return decorator


# =============================================================================
# Workflow Mixin for Models
# =============================================================================

class WorkflowMixin:
    """
    Mixin to add workflow capabilities to Django models.
    
    Usage:
        class Quote(WorkflowMixin, models.Model):
            status = ChoiceEnumField(enum_type=QuoteStatus)
            
            class Workflow:
                state_field = 'status'
                
                transitions = [
                    Transition(
                        source=QuoteStatus.DRAFT,
                        target=QuoteStatus.SENT,
                        trigger='send'
                    ),
                ]
    """
    
    _state_field = 'status'
    _workflow_class = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state_machine = None
    
    @property
    def state_machine(self):
        """Get or create state machine instance."""
        if self._state_machine is None:
            workflow_cls = getattr(self, 'Workflow', None)
            if workflow_cls:
                # Build state machine class from Workflow definition
                state_field = getattr(workflow_cls, 'state_field', 'status')
                transitions = getattr(workflow_cls, 'transitions', [])
                
                # Create dynamic state machine class
                class DynamicStateMachine(StateMachine):
                    _transitions = transitions
                    _states = set()
                
                for t in transitions:
                    DynamicStateMachine._states.add(t.source_value)
                    DynamicStateMachine._states.add(t.target_value)
                
                self._state_machine = DynamicStateMachine(self, state_field)
        
        return self._state_machine
    
    def can_transition_to(self, target) -> bool:
        """Check if transition to target is possible."""
        sm = self.state_machine
        return sm.can_transition(target) if sm else False
    
    def get_available_triggers(self) -> List[str]:
        """Get list of available trigger names."""
        sm = self.state_machine
        return sm.available_triggers if sm else []
    
    def transition(self, target, *args, **kwargs) -> bool:
        """Execute transition to target state."""
        sm = self.state_machine
        if not sm:
            raise StateMachineError("No workflow defined for this model")
        return sm.transition_to(target, *args, **kwargs)
    
    def execute_trigger(self, trigger_name: str, *args, **kwargs) -> bool:
        """Execute a workflow trigger."""
        sm = self.state_machine
        if not sm:
            raise StateMachineError("No workflow defined for this model")
        return sm.trigger(trigger_name, *args, **kwargs)


# =============================================================================
# Predefined Workflow State Machines
# =============================================================================

class QuoteWorkflow(StateMachine):
    """Workflow for Quote entities."""
    
    from core.enums import QuoteStatus
    
    # Draft state transitions
    draft_to_sent = Transition(
        source=QuoteStatus.DRAFT,
        target=QuoteStatus.SENT,
        trigger='send'
    )
    draft_to_cancelled = Transition(
        source=QuoteStatus.DRAFT,
        target=QuoteStatus.CANCELLED,
        trigger='cancel'
    )
    
    # Sent state transitions
    sent_to_pending = Transition(
        source=QuoteStatus.SENT,
        target=QuoteStatus.PENDING,
        trigger='mark_pending'
    )
    sent_to_accepted = Transition(
        source=QuoteStatus.SENT,
        target=QuoteStatus.ACCEPTED,
        trigger='accept'
    )
    sent_to_rejected = Transition(
        source=QuoteStatus.SENT,
        target=QuoteStatus.REJECTED,
        trigger='reject'
    )
    
    # Pending state transitions
    pending_to_accepted = Transition(
        source=QuoteStatus.PENDING,
        target=QuoteStatus.ACCEPTED,
        trigger='accept'
    )
    pending_to_rejected = Transition(
        source=QuoteStatus.PENDING,
        target=QuoteStatus.REJECTED,
        trigger='reject'
    )
    pending_to_expired = Transition(
        source=QuoteStatus.PENDING,
        target=QuoteStatus.EXPIRED,
        trigger='expire'
    )
    
    # Accepted state transitions
    accepted_to_converted = Transition(
        source=QuoteStatus.ACCEPTED,
        target=QuoteStatus.CONVERTED,
        trigger='convert_to_invoice'
    )


class InvoiceWorkflow(StateMachine):
    """Workflow for Invoice entities."""
    
    from core.enums import InvoiceStatus
    
    # Draft state transitions
    draft_to_sent = Transition(
        source=InvoiceStatus.DRAFT,
        target=InvoiceStatus.SENT,
        trigger='send'
    )
    draft_to_cancelled = Transition(
        source=InvoiceStatus.DRAFT,
        target=InvoiceStatus.CANCELLED,
        trigger='cancel'
    )
    draft_to_approved = Transition(
        source=InvoiceStatus.DRAFT,
        target=InvoiceStatus.APPROVED,
        trigger='approve'
    )
    
    # Approved state transitions
    approved_to_sent = Transition(
        source=InvoiceStatus.APPROVED,
        target=InvoiceStatus.SENT,
        trigger='send'
    )
    
    # Sent state transitions
    sent_to_pending = Transition(
        source=InvoiceStatus.SENT,
        target=InvoiceStatus.PENDING,
        trigger='mark_pending'
    )
    
    # Pending state transitions
    pending_to_partially_paid = Transition(
        source=InvoiceStatus.PENDING,
        target=InvoiceStatus.PARTIALLY_PAID,
        trigger='record_partial_payment'
    )
    pending_to_paid = Transition(
        source=InvoiceStatus.PENDING,
        target=InvoiceStatus.PAID,
        trigger='record_payment'
    )
    pending_to_overdue = Transition(
        source=InvoiceStatus.PENDING,
        target=InvoiceStatus.OVERDUE,
        trigger='mark_overdue'
    )
    pending_to_disputed = Transition(
        source=InvoiceStatus.PENDING,
        target=InvoiceStatus.DISPUTED,
        trigger='dispute'
    )
    
    # Partially paid transitions
    partially_paid_to_paid = Transition(
        source=InvoiceStatus.PARTIALLY_PAID,
        target=InvoiceStatus.PAID,
        trigger='record_payment'
    )
    partially_paid_to_overdue = Transition(
        source=InvoiceStatus.PARTIALLY_PAID,
        target=InvoiceStatus.OVERDUE,
        trigger='mark_overdue'
    )
    
    # Disputed transitions
    disputed_to_pending = Transition(
        source=InvoiceStatus.DISPUTED,
        target=InvoiceStatus.PENDING,
        trigger='resolve_dispute'
    )
    
    # Final states (can be cancelled)
    sent_to_cancelled = Transition(
        source=InvoiceStatus.SENT,
        target=InvoiceStatus.CANCELLED,
        trigger='cancel'
    )
    pending_to_cancelled = Transition(
        source=InvoiceStatus.PENDING,
        target=InvoiceStatus.CANCELLED,
        trigger='cancel'
    )


class OrderWorkflow(StateMachine):
    """Workflow for Order entities."""
    
    from core.enums import OrderStatus
    
    # Pending state transitions
    pending_to_confirmed = Transition(
        source=OrderStatus.PENDING,
        target=OrderStatus.CONFIRMED,
        trigger='confirm'
    )
    pending_to_cancelled = Transition(
        source=OrderStatus.PENDING,
        target=OrderStatus.CANCELLED,
        trigger='cancel'
    )
    
    # Confirmed state transitions
    confirmed_to_processing = Transition(
        source=OrderStatus.CONFIRMED,
        target=OrderStatus.PROCESSING,
        trigger='start_processing'
    )
    confirmed_to_on_hold = Transition(
        source=OrderStatus.CONFIRMED,
        target=OrderStatus.ON_HOLD,
        trigger='hold'
    )
    confirmed_to_cancelled = Transition(
        source=OrderStatus.CONFIRMED,
        target=OrderStatus.CANCELLED,
        trigger='cancel'
    )
    
    # Processing state transitions
    processing_to_shipped = Transition(
        source=OrderStatus.PROCESSING,
        target=OrderStatus.SHIPPED,
        trigger='ship'
    )
    processing_to_on_hold = Transition(
        source=OrderStatus.PROCESSING,
        target=OrderStatus.ON_HOLD,
        trigger='hold'
    )
    
    # On hold transitions
    on_hold_to_processing = Transition(
        source=OrderStatus.ON_HOLD,
        target=OrderStatus.PROCESSING,
        trigger='resume'
    )
    on_hold_to_cancelled = Transition(
        source=OrderStatus.ON_HOLD,
        target=OrderStatus.CANCELLED,
        trigger='cancel'
    )
    
    # Shipped state transitions
    shipped_to_delivered = Transition(
        source=OrderStatus.SHIPPED,
        target=OrderStatus.DELIVERED,
        trigger='deliver'
    )
    
    # Delivered state transitions
    delivered_to_refunded = Transition(
        source=OrderStatus.DELIVERED,
        target=OrderStatus.REFUNDED,
        trigger='refund'
    )


class ProjectWorkflow(StateMachine):
    """Workflow for Project entities."""
    
    from core.enums import ProjectStatus
    
    # Planning state transitions
    planning_to_pre_construction = Transition(
        source=ProjectStatus.PLANNING,
        target=ProjectStatus.PRE_CONSTRUCTION,
        trigger='start_pre_construction'
    )
    planning_to_cancelled = Transition(
        source=ProjectStatus.PLANNING,
        target=ProjectStatus.CANCELLED,
        trigger='cancel'
    )
    planning_to_on_hold = Transition(
        source=ProjectStatus.PLANNING,
        target=ProjectStatus.ON_HOLD,
        trigger='hold'
    )
    
    # Pre-construction transitions
    pre_construction_to_under_construction = Transition(
        source=ProjectStatus.PRE_CONSTRUCTION,
        target=ProjectStatus.UNDER_CONSTRUCTION,
        trigger='start_construction'
    )
    pre_construction_to_on_hold = Transition(
        source=ProjectStatus.PRE_CONSTRUCTION,
        target=ProjectStatus.ON_HOLD,
        trigger='hold'
    )
    
    # Under construction transitions
    under_construction_to_completed = Transition(
        source=ProjectStatus.UNDER_CONSTRUCTION,
        target=ProjectStatus.COMPLETED,
        trigger='complete_construction'
    )
    under_construction_to_renovating = Transition(
        source=ProjectStatus.UNDER_CONSTRUCTION,
        target=ProjectStatus.RENOVATING,
        trigger='start_renovation'
    )
    under_construction_to_on_hold = Transition(
        source=ProjectStatus.UNDER_CONSTRUCTION,
        target=ProjectStatus.ON_HOLD,
        trigger='hold'
    )
    
    # Completed transitions
    completed_to_selling = Transition(
        source=ProjectStatus.COMPLETED,
        target=ProjectStatus.SELLING,
        trigger='start_sales'
    )
    
    # Selling transitions
    selling_to_sold_out = Transition(
        source=ProjectStatus.SELLING,
        target=ProjectStatus.SOLD_OUT,
        trigger='sell_out'
    )
    selling_to_renovating = Transition(
        source=ProjectStatus.SELLING,
        target=ProjectStatus.RENOVATING,
        trigger='renovate'
    )
    
    # On hold transitions
    on_hold_to_planning = Transition(
        source=ProjectStatus.ON_HOLD,
        target=ProjectStatus.PLANNING,
        trigger='resume'
    )
    on_hold_to_pre_construction = Transition(
        source=ProjectStatus.ON_HOLD,
        target=ProjectStatus.PRE_CONSTRUCTION,
        trigger='resume_pre_construction'
    )
    on_hold_to_under_construction = Transition(
        source=ProjectStatus.ON_HOLD,
        target=ProjectStatus.UNDER_CONSTRUCTION,
        trigger='resume_construction'
    )