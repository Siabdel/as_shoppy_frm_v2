from datetime import datetime
from django.utils import timezone
import uuid
from django.utils.text import slugify
from django.db import models
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from core.base_product import models as base_models
from polymorphic.models import PolymorphicModel, PolymorphicManager
from mptt.models import MPTTModel, TreeForeignKey
from core.profile.models import Societe
from core.taxonomy.models import TaggedItem, MPCategory
# from mapwidgets.widgets import GooglePointField
##from django.contrib.gis.db import models as gmodels
from core import deferred
from enum import Enum

# Create your models here.
class Partenaire(models.Model):
    tiers_id    = models.CharField(max_length=3)
    tiers_name  = models.CharField(max_length=100)
    tiers_type  = models.CharField(max_length=1, choices=(('C', 'Client'), ('F', 'Fornisseur')), default='F')
    created     = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # Listed below are the mandatory fields for a generic relation
    content_type    = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id       = models.PositiveIntegerField()
    content_object  = GenericForeignKey('content_type', 'object_id')


    def __str__(self):
        return "tiers=%s id=%s" % (self.tiers_type , self.tiers_id)
class ProjectStatus(Enum):
    PLANNING = 'PLANNING', _('En planification')
    PRE_CONSTRUCTION = 'PRE_CONSTRUCTION', _('Pré-construction')
    UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', _('En construction')
    COMPLETED = 'COMPLETED', _('Terminé')
    SELLING = 'SELLING', _('En vente')
    SOLD_OUT = 'SOLD_OUT', _('Vendu')
    CANCELLED = 'CANCELLED', _('Annulé')
    ON_HOLD = 'ON_HOLD', _('En attente')
    RENOVATING = 'RENOVATING', _('En rénovation')
    
    def __init__(self, code, label):
        self.code = code
        self.label = label

    @classmethod
    def choices(cls):
        return [(item.code, item.label) for item in cls]

class Project(base_models.BaseProject):
    code = models.CharField(max_length=50, unique=True, editable=False)
    societe = models.ForeignKey(Societe, on_delete=models.CASCADE)
    category = models.ForeignKey(MPCategory, related_name='projetcs', null=True, blank=True, on_delete=models.CASCADE)
    partenaire  = GenericRelation(Partenaire, null=True, blank=True) # clients ou fournisseurs
    documents   = GenericRelation('taxonomy.GDocument',  null=True, blank=True) #  les documents rattachées
    lon = models.FloatField(null=True, blank=True) # longitude
    lat = models.FloatField(null=True, blank=True) # latitude
    active = models.BooleanField(default=True)
    status = status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices(),
        default=ProjectStatus.PLANNING.code,
        verbose_name=_("Statut du project"),
    )
    #location = gmodels.PointField(null=True, blank=True)

    def generate_project_number(self):
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        unique_id = str(uuid.uuid4())[:7].upper()
        # Générer le numéro de facture
        # Nous utilisons self.pk pour l'ID de la facture, qui sera disponible après la sauvegarde initiale
        new_number = f"PRJ-{year}{month}{day}-{self.pk:03d}-{unique_id}"
        return new_number


    def save(self, *args, **kwargs):
        # Sauvegarder d'abord pour obtenir un ID (self.pk)
        super().save(*args, **kwargs)
        
        # Générer et sauvegarder le numéro de facture si ce n'est pas déjà fait
        if not self.code:
            self.code = self.generate_project_number()
            super().save(update_fields=['code'])
        # super save
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Project {self.code} - {self.status}"

    


class ProjectImage(base_models.BaseImage) :
    project = models.ForeignKey(Project, related_name='images', null=True, blank=True, on_delete=models.CASCADE)


class Task(models.Model):
    """Task model for project management."""
    
    from core.enums import TaskStatus, TaskPriority, TaskType
    
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    project = models.ForeignKey(Project, related_name='tasks', on_delete=models.CASCADE, verbose_name=_("Project"))
    created_by = models.ForeignKey('auth.User', related_name='created_tasks', on_delete=models.CASCADE, verbose_name=_("Created by"))
    assigned_to = models.ForeignKey('auth.User', related_name='assigned_tasks', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Assigned to"))
    
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.default.value,
        verbose_name=_("Status")
    )
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.default.value,
        verbose_name=_("Priority")
    )
    task_type = models.CharField(
        max_length=20,
        choices=TaskType.choices,
        default=TaskType.default.value,
        verbose_name=_("Task Type")
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Completed at"))
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Due date"))
    
    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"


class Ticket(models.Model):
    """Ticket/Issue model for project management."""
    
    from core.enums import TicketStatus, TicketPriority, TicketType
    
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    project = models.ForeignKey(Project, related_name='tickets', on_delete=models.CASCADE, verbose_name=_("Project"))
    created_by = models.ForeignKey('auth.User', related_name='created_tickets', on_delete=models.CASCADE, verbose_name=_("Created by"))
    assigned_to = models.ForeignKey('auth.User', related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Assigned to"))
    
    status = models.CharField(
        max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.default.value,
        verbose_name=_("Status")
    )
    priority = models.CharField(
        max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.default.value,
        verbose_name=_("Priority")
    )
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketType.choices,
        default=TicketType.default.value,
        verbose_name=_("Ticket Type")
    )
    
    resolution = models.TextField(blank=True, verbose_name=_("Resolution"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Resolved at"))
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Due date"))
    
    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"