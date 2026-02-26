from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum, F
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from customer.models import Customer
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext as _
from product import models as pro_models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from devis.models import Quote

def get_default_expiration_date():
    return timezone.now() + timedelta(days=30)

from enum import Enum

class StatutFacture(Enum):
    BROUILLON = ('brouillon', _('Brouillon'))
    ENVOYEE = ('envoyée', _('Envoyée'))
    EN_ATTENTE = ('en_attente', _('En attente'))
    PARTIELLEMENT_PAYEE = ('partiellement_payée', _('Partiellement payée'))
    PAYEE = ('payée', _('Payée'))
    EN_RETARD = ('en_retard', _('En retard'))
    ANNULEE = ('annulée', _('Annulée'))
    REMBOURSEE = ('remboursée', _('Remboursée'))
    CONTESTEE = ('contestée', _('Contestée'))
    ABANDONNEE = ('abandonnée', _('Abandonnée'))
    APPROUVEE = ('approuvée', _('Approuvée'))
    EN_COURS_DE_TRAITEMENT = ('en_cours_de_traitement', _('En cours de traitement'))
    ECHUE = ('échue', _('Échue'))
    CREDIT = ('crédit', _('Crédit'))

    def __init__(self, code, label):
        self.code = code
        self.label = label

    @classmethod
    def choices(cls):
        return [(item.code, item.label) for item in cls]

class Invoice(models.Model):
    client = models.ForeignKey(Customer, on_delete=models.CASCADE)
    numero = models.CharField(max_length=50, unique=True, editable=False)
    devis_source = models.ForeignKey(Quote, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Devis source"))

    # Champ pour le statut utilisant l'énumération
    
    status = models.CharField(
        max_length=50,
        choices=StatutFacture.choices(),
        default=StatutFacture.BROUILLON.code    ,
        verbose_name=_("Statut de la facture")
    )
    invoice_total = models.DecimalField(
        max_digits=10, decimal_places=2, 
        blank=True, null=True, editable=False, default=0
    )
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    created_at = models.DateField(auto_now_add=True)
    expiration_date = models.DateTimeField(default=get_default_expiration_date)
   
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_terms = models.TextField(
        blank=True,
        default="NET 30 Days. Finance Charge of 1.5% will be \
        made on unpaid balances after 30 days.",
    )
    completed = models.BooleanField(default=False) # invoice valide qui n'est pas vide de items

    class Meta:
        verbose_name: "Invoice"
        verbose_name_plural: "Invoices"  # noqa F821

    def get_absolute_url(self):
        return reverse("invoice-detail", kwargs={"pk": self.pk})

    def get_invoice_total(self):
        if self.pk:
            total = self.items.aggregate(invoice_total=Sum(F('quantity') * F('price'))).get('invoice_total', 0)
            return total
        return self.invoice_total
     # Méthodes pour changer le statut
     # Méthodes pour changer le statut
    def marquer_comme_envoyee(self):
        self.statut = StatutFacture.ENVOYEE.code
        self.save()

    def marquer_comme_payee(self):
        self.statut = StatutFacture.PAYEE.code
        self.save()
        
    
    def generate_invoice_number(self):
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        # Générer le numéro de facture
        # Nous utilisons self.pk pour l'ID de la facture, qui sera disponible après la sauvegarde initiale
        new_number = f"INV-{year}{month}{day}-{self.client.pk:04d}-{self.pk:06d}"
        return new_number

    def save(self, *args, **kwargs):
        # Sauvegarder d'abord pour obtenir un ID (self.pk)
        super().save(*args, **kwargs)
        
        # Générer et sauvegarder le numéro de facture si ce n'est pas déjà fait
        if not self.numero:
            self.numero = self.generate_invoice_number()
            super().save(update_fields=['numero'])

        
        # Générer et sauvegarder le numéro de facture si ce n'est pas déjà fait
        if not self.numero:
            self.numero = self.generate_invoice_number()
            super().save(update_fields=['numero'])

    def __str__(self):
        return f"Invoice #{self.pk} for {self.client}"

    def __repr__(self):
        return f"<Invoice: {self.pk} - {self.client}>"

    def update_invoice_total(self):
        self.invoice_total = self.get_invoice_total()
        self.save(update_fields=['invoice_total'])


   
class InvoiceItem(models.Model):
    # Invoice Line Items
    invoice = models.ForeignKey("Invoice", related_name=_("items"), on_delete=models.CASCADE)
    product = models.ForeignKey(pro_models.Product, related_name=_("pro_items"), on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=True, blank=True)
    class Meta:
        verbose_name: "Invoice_Item"
        verbose_name_plural: "Invoice_Items"

    def __str__(self):
        return f"{self.product} _ {self.subtotal}"

    def __repr__(self):
        return f"<Invoice Line Item: {self.product} - {self.subtotal}>"

    @property
    def subtotal(self):
        return self.quantity * self.product.price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_invoice_total()

# Signal handlers
@receiver(post_save, sender=InvoiceItem)
@receiver(post_delete, sender=InvoiceItem)
def update_invoice_total(sender, instance, **kwargs):
    instance.invoice.update_invoice_total()
