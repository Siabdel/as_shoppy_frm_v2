from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from enum import Enum
from customer.models import Customer
from product.models import Product

class StatutDevis(Enum):
    BROUILLON = ('brouillon', _('Brouillon'))
    ENVOYE = ('envoyé', _('Envoyé'))
    EN_ATTENTE = ('en_attente', _('En attente'))
    ACCEPTE = ('accepté', _('Accepté'))
    REFUSE = ('refusé', _('Refusé'))
    EXPIRE = ('expiré', _('Expiré'))
    CONVERTI = ('converti', _('Converti en facture'))

    def __init__(self, code, label):
        self.code = code
        self.label = label

    @classmethod
    def choices(cls):
        return [(item.code, item.label) for item in cls]

  
class Quote(models.Model):
    numero = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    date_expiration = models.DateField()
    client = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name=_("Client"))
    total_amount= models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant total"))
    status = models.CharField(
        max_length=50,
        choices=StatutDevis.choices(),
        default=StatutDevis.BROUILLON.code,
        verbose_name=_("Statut du devis")
    )
    completed = models.BooleanField(default=False)
    quote_terms = models.TextField(blank=True, verbose_name=_("Quote_terms"))

    @classmethod
    def generate_quote_number(cls, client_pk, quote_pk):
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        return f"QUO-{year}{month}{day}-{client_pk:04d}-{quote_pk:06d}"

    def save(self, *args, **kwargs):
        if not self.numero:
            super().save(*args, **kwargs)  # Save to get a PK
            self.numero = self.generate_quote_number(self.client.pk, self.pk)
            return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Devis {self.numero} - {self.get_statut_display()}"

    class Meta:
        verbose_name = _("Devis")
        verbose_name_plural = _("Devis")

    def marquer_comme_envoye(self):
        self.statut = StatutDevis.ENVOYE.code
        self.save()

    def marquer_comme_accepte(self):
        self.statut = StatutDevis.ACCEPTE.code
        self.save()

    def marquer_comme_refuse(self):
        self.statut = StatutDevis.REFUSE.code
        self.save()

    def convertir_en_facture(self):
        if self.statut == StatutDevis.ACCEPTE.code:
            # Créer une nouvelle facture basée sur ce devis
            facture = Invoice.objects.create(
                client=self.client,
                total_amount=self.total_amount,
                description=self.description,
                devis_source=self
            )
            self.statut = StatutDevis.CONVERTI.code
            self.save()
            return facture
        else:
            raise ValueError(_("Seuls les devis acceptés peuvent être convertis en factures."))

# Maintenant, ajoutons une référence au devis dans le modèle Invoice

  
   
class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="quote_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=6, decimal_places=2, default=0, null=True, blank=True)

    class Meta:
        verbose_name = _("Élément de devis")
        verbose_name_plural = _("Éléments de devis")

    def __str__(self):
        return f"{self.product} - {self.subtotal}"
    
    def update_quote_total(self):
        self.quote_total = sum(item.quantity * item.price for item in self.items.all())
        self.save()
    
    @property
    def subtotal(self):
        return self.quantity * self.price
    