"""
Core Enumerations Module

Centralizes all enum definitions used across the application.
Provides consistent choices for models, forms, and API responses.
"""

import enum
from django.utils.translation import gettext_lazy as _
from django.db import models


class ChoiceEnumMeta(enum.EnumMeta):
    """Metaclass for ChoiceEnum providing Django-compatible choices."""
    
    def __call__(cls, value, *args, **kwargs):
        if isinstance(value, str):
            try:
                value = cls.__members__[value]
            except KeyError:
                pass
        return super().__call__(value, *args, **kwargs)

    def __new__(metacls, classname, bases, classdict):
        labels = {}
        for key in list(classdict._member_names):
            source_value = classdict[key]
            if isinstance(source_value, (list, tuple)):
                try:
                    val, labels[key] = source_value
                except ValueError:
                    raise ValueError(f"Invalid ChoiceEnum member '{key}'")
            else:
                val = source_value
                labels[key] = key.replace("_", " ").title()
            dict.__setitem__(classdict, key, val)
        cls = super().__new__(metacls, classname, bases, classdict)
        for key, label in labels.items():
            getattr(cls, key).label = label
        return cls

    @property
    def choices(cls):
        return [(k.value, k.label) for k in cls]

    @property
    def default(cls):
        try:
            return next(iter(cls))
        except StopIteration:
            return None


class ChoiceEnum(enum.Enum, metaclass=ChoiceEnumMeta):
    """
    Base utility class for handling choices in Django models and forms.
    
    Usage:
        class Color(ChoiceEnum):
            WHITE = 0, "White"
            RED = 1, "Red"
    
        color = forms.ChoiceField(choices=Color.choices, default=Color.default)
    """
    def __str__(self):
        return str(self.label)


# =============================================================================
# Customer & User Enums
# =============================================================================

class CustomerState(ChoiceEnum):
    """Customer recognition states."""
    UNRECOGNIZED = 0, _("Unrecognized")
    GUEST = 1, _("Guest")
    REGISTERED = 2, _("Registered")


# =============================================================================
# Order & Commerce Enums
# =============================================================================

class OrderStatus(ChoiceEnum):
    """Order lifecycle states."""
    PENDING = 'pending', _("Pending")
    CONFIRMED = 'confirmed', _("Confirmed")
    PROCESSING = 'processing', _("Processing")
    SHIPPED = 'shipped', _("Shipped")
    DELIVERED = 'delivered', _("Delivered")
    CANCELLED = 'cancelled', _("Cancelled")
    REFUNDED = 'refunded', _("Refunded")
    ON_HOLD = 'on_hold', _("On Hold")


class PaymentStatus(ChoiceEnum):
    """Payment processing states."""
    PENDING = 'pending', _("Pending")
    AUTHORIZED = 'authorized', _("Authorized")
    CAPTURED = 'captured', _("Captured")
    FAILED = 'failed', _("Failed")
    REFUNDED = 'refunded', _("Refunded")
    PARTIALLY_REFUNDED = 'partially_refunded', _("Partially Refunded")


# =============================================================================
# Quote (Devis) Enums
# =============================================================================

class QuoteStatus(ChoiceEnum):
    """Quote lifecycle states."""
    DRAFT = 'draft', _("Draft")
    SENT = 'sent', _("Sent")
    PENDING = 'pending', _("Pending")
    ACCEPTED = 'accepted', _("Accepted")
    REJECTED = 'rejected', _("Rejected")
    EXPIRED = 'expired', _("Expired")
    CONVERTED = 'converted', _("Converted to Invoice")
    CANCELLED = 'cancelled', _("Cancelled")


# =============================================================================
# Invoice Enums
# =============================================================================

class InvoiceStatus(ChoiceEnum):
    """Invoice lifecycle states."""
    DRAFT = 'draft', _("Draft")
    SENT = 'sent', _("Sent")
    PENDING = 'pending', _("Pending")
    PARTIALLY_PAID = 'partially_paid', _("Partially Paid")
    PAID = 'paid', _("Paid")
    OVERDUE = 'overdue', _("Overdue")
    CANCELLED = 'cancelled', _("Cancelled")
    REFUNDED = 'refunded', _("Refunded")
    DISPUTED = 'disputed', _("Disputed")
    ABANDONED = 'abandoned', _("Abandoned")
    APPROVED = 'approved', _("Approved")
    PROCESSING = 'processing', _("Processing")
    WRITTEN_OFF = 'written_off', _("Written Off")
    CREDIT_NOTE = 'credit_note', _("Credit Note")


# =============================================================================
# Project Management Enums
# =============================================================================

class ProjectStatus(ChoiceEnum):
    """Project lifecycle states."""
    PLANNING = 'planning', _("Planning")
    PRE_CONSTRUCTION = 'pre_construction', _("Pre-Construction")
    UNDER_CONSTRUCTION = 'under_construction', _("Under Construction")
    COMPLETED = 'completed', _("Completed")
    SELLING = 'selling', _("Selling")
    SOLD_OUT = 'sold_out', _("Sold Out")
    CANCELLED = 'cancelled', _("Cancelled")
    ON_HOLD = 'on_hold', _("On Hold")
    RENOVATING = 'renovating', _("Renovating")


class ProjectVisibility(ChoiceEnum):
    """Project visibility levels."""
    PUBLIC = 'public', _("Public Project")
    INTERNAL = 'internal', _("Internal Project")
    CLIENT = 'client', _("Client-Linked Project")
    PRIVATE = 'private', _("Private (Subscribers Only)")


class TicketStatus(ChoiceEnum):
    """Ticket/issue tracking states."""
    NEW = 'new', _("New")
    IN_PROGRESS = 'in_progress', _("In Progress")
    RESOLVED = 'resolved', _("Resolved")
    CLOSED = 'closed', _("Closed")
    CANCELLED = 'cancelled', _("Cancelled")
    ON_HOLD = 'on_hold', _("On Hold")


class TicketPriority(ChoiceEnum):
    """Ticket priority levels."""
    LOW = 'low', _("Low")
    MEDIUM = 'medium', _("Medium")
    HIGH = 'high', _("High")
    CRITICAL = 'critical', _("Critical")


class TicketType(ChoiceEnum):
    """Ticket classification types."""
    BUG = 'bug', _("Bug")
    TASK = 'task', _("Task")
    IDEA = 'idea', _("Idea")
    FEATURE = 'feature', _("Feature Request")
    SUPPORT = 'support', _("Support")


class TaskStatus(ChoiceEnum):
    """Task tracking states."""
    NEW = 'new', _("New")
    IN_PROGRESS = 'in_progress', _("In Progress")
    COMPLETED = 'completed', _("Completed")
    CLOSED = 'closed', _("Closed")
    CANCELLED = 'cancelled', _("Cancelled")
    ON_HOLD = 'on_hold', _("On Hold")


class TaskPriority(ChoiceEnum):
    """Task priority levels (Agile methodology)."""
    OPTIONAL = 'optional', _("Optional")
    LOW = 'low', _("Low")
    IMPORTANT = 'important', _("Important")
    URGENT = 'urgent', _("Urgent")


class TaskType(ChoiceEnum):
    """Task classification types."""
    ACTION = 'action', _("Action")
    TASK = 'task', _("Task")
    IDEA = 'idea', _("Idea")
    MILESTONE = 'milestone', _("Milestone")


# =============================================================================
# Product & Catalog Enums
# =============================================================================

class ProductStatus(ChoiceEnum):
    """Product availability states."""
    AVAILABLE = 'available', _("Available")
    OUT_OF_STOCK = 'out_of_stock', _("Out of Stock")
    DISCONTINUED = 'discontinued', _("Discontinued")
    COMING_SOON = 'coming_soon', _("Coming Soon")
    PRE_ORDER = 'pre_order', _("Pre-Order")


# =============================================================================
# Legacy Compatibility Aliases
# =============================================================================

# These aliases maintain backward compatibility with existing code
StatutDevis = QuoteStatus
StatutFacture = InvoiceStatus


# =============================================================================
# Django Model Field for ChoiceEnum
# =============================================================================

class ChoiceEnumField(models.CharField):
    """
    Django model field for ChoiceEnum types.
    Automatically handles choices and defaults.
    """
    description = _("Choice Enum Field")
    
    def __init__(self, *args, **kwargs):
        self.enum_type = kwargs.pop('enum_type', ChoiceEnum)
        if not issubclass(self.enum_type, ChoiceEnum):
            raise ValueError("enum_type must be a subclass of ChoiceEnum")
        
        kwargs.setdefault('max_length', 50)
        kwargs.update(choices=self.enum_type.choices)
        if self.enum_type.default:
            kwargs.setdefault('default', self.enum_type.default.value)
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'choices' in kwargs:
            del kwargs['choices']
        if 'default' in kwargs and self.enum_type.default:
            if kwargs['default'] == self.enum_type.default.value:
                del kwargs['default']
        return name, path, args, kwargs
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.enum_type(value)
        except ValueError:
            return value
    
    def get_prep_value(self, value):
        if isinstance(value, self.enum_type):
            return value.value
        return value
    
    def to_python(self, value):
        if value is None or isinstance(value, self.enum_type):
            return value
        return self.enum_type(value)


class IntegerChoiceEnumField(models.PositiveSmallIntegerField):
    """
    Integer-based Django model field for ChoiceEnum types.
    """
    description = _("Integer Choice Enum Field")
    
    def __init__(self, *args, **kwargs):
        self.enum_type = kwargs.pop('enum_type', ChoiceEnum)
        if not issubclass(self.enum_type, ChoiceEnum):
            raise ValueError("enum_type must be a subclass of ChoiceEnum")
        
        kwargs.update(choices=self.enum_type.choices)
        if self.enum_type.default:
            kwargs.setdefault('default', self.enum_type.default.value)
        super().__init__(*args, **kwargs)
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if 'choices' in kwargs:
            del kwargs['choices']
        if 'default' in kwargs and self.enum_type.default:
            if kwargs['default'] == self.enum_type.default.value:
                del kwargs['default']
        return name, path, args, kwargs
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return self.enum_type(value)
        except ValueError:
            return value
    
    def get_prep_value(self, value):
        if isinstance(value, self.enum_type):
            return value.value
        return value
    
    def to_python(self, value):
        if value is None or isinstance(value, self.enum_type):
            return value
        return self.enum_type(value)