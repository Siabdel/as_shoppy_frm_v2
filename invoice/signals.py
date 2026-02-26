from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice, InvoiceItem
from shop.models import ShopCart

@receiver(post_save, sender=InvoiceItem)
def set_invoice_total(sender, instance, **kwargs):
    total = instance.invoice.items.aggregate(
        invoice_total=Sum(F("quantity") * F("rate"))
    ).get("invoice_total", 0)
    if total:
        Invoice.objects.filter(pk=instance.invoice.pk).update(invoice_total=total)


@receiver(post_save, sender=Invoice)
# Define a function to empty the cart whene invoice created & completed
def empty_cart(sender, instance, **kwargs):
    # Assuming you have a Cart model associated with the user
    cart = ShopCart.objects.get(created_by=instance.client.created_by)
    if instance.completed :
        cart.empty()  # Remove all items from the cart
#---
def set_invoiceitem_total(sender, instance, **kwargs):
    if len(instance.items.all()) > 0:
        total = instance.items.aggregate(
            invoice_total=Sum(F("quantity") * F("rate"))
        ).get("invoice_total", 0)
        if total:
            Invoice.objects.filter(pk=instance.pk).update(invoice_total=total)




# Connect the signal to the function
#@receiver(checkout_completed)
def handle_checkout_completed(sender, user, **kwargs):
    empty_cart(user)