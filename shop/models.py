
from django.db.models import SET_DEFAULT
from django.utils import timezone
from core import deferred
from core.models.address import BaseShippingAddress, BaseBillingAddress
from core.base_shop.models import BaseCart, BaseCartItem, CartItemModel
from django.db import models
from product import models as pro_models
from customer.models import Customer
from polymorphic.models import PolymorphicModel, PolymorphicManager


class CartItem(BaseCartItem):
    """Default materialized model for CartItem"""
    product = models.ForeignKey(pro_models.Product, on_delete=models.CASCADE,)
    quantity = models.PositiveIntegerField()

    @property
    def total_price(self):
        return self.quantity * self.product.price

class ShopCart(BaseCart):
    """
    Default materialized model for BaseCart containing common fields
    """
    shipping_address = deferred.ForeignKey(
        BaseShippingAddress,
        on_delete=SET_DEFAULT,
        null=True,
        default=None,
        related_name='+',
    )

    billing_address = deferred.ForeignKey(
        BaseBillingAddress,
        on_delete=SET_DEFAULT,
        null=True,
        default=None,
        related_name='+',
    )
    
    def add_product(self, product, quantity=1):
        """
        Ajoute un produit au panier ou met à jour sa quantité si déjà présent.
        
        :param product: L'instance du produit à ajouter
        :param quantity: La quantité à ajouter (par défaut 1)
        :return: L'item du panier (CartItem) créé ou mis à jour
        """
        # Utilisez customer ici
        #customer = Customer.objects.get_from_request(request)
        # Utilisez customer ici
        if not isinstance(product, pro_models.Product):
            raise ValueError("Le produit doit être une instance de pro_models.Product")

        if quantity <= 0:
            raise ValueError("La quantité doit être supérieure à zéro")

        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        self.updated_at = timezone.now()
        self.save()

        return cart_item