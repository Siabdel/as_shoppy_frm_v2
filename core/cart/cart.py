# -*- coding:UTF-8 -*-
import datetime
import math
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.models import User, AnonymousUser
from product import models as pro_models
from shop import models as sh_models
from core.utils import get_product_model
from django.contrib.contenttypes.models import ContentType

class Cart(object):
    def __init__(self, request, product_model=None):
        self.session = request.session
        self.request = request
        self.cart = self.session[settings.CART_SESSION_ID] = {}
        #raise Exception(f"Model == { self.product_model }")
        # 1. user enregistre
        # 2. user AnonymousUser 
                # creer un cart 
        # 3. pas de User
        #
        self.product_model = product_model if product_model else get_product_model()
        # on trouve un dans la session            
        self.cart = self.session.get(settings.CART_SESSION_ID)
        
        if self.cart:
            try:
                self.cart = sh_models.ShopCart.objects.filter(created_by=request.user).last()
            except Exception as err:
                self.cart = self.new(request)
        
        elif request.user == AnonymousUser():
            self.cart = self.session[settings.CART_SESSION_ID] = {}
        else :
            self.cart = self.session[settings.CART_SESSION_ID] = {}
            self.cart = self.new_cart(request)
    
    def new_cart(self, request):
        self.cart = sh_models.ShopCart.objects.get_or_create_cart(request.user)
        # session init
        request.session[settings.CART_SESSION_ID] = self.cart.id
        # messages.add_message(self.request, messages.INFO, 'on cree un panier .%s' % self.cart.id)
        return self.cart

    def add(self, product, quantity=1, update_quantity=False):
        #
        # Vérifiez si un article pour ce produit existe déjà dans le panier
        #messages.add_message(self.request, messages.INFO,
        #                     f"item quantite={product.price} updatea= {update_quantity}"  )
        try :
            item = sh_models.CartItem.objects.get(
                                            cart=self.cart, 
                                            product=product,
                                            )
            if update_quantity:
                item.quantity = quantity             
            else :
                item.quantity += quantity             
            
            item.save()
        
        except Exception as err:
            item, created = sh_models.CartItem.objects.get_or_create(
                                    cart=self.cart,
                                    product=product,
                                    quantity=quantity,
                                    unit_price = product.price,
                                    defaults={'quantity': 1, 'unit_price': product.price}
                                    )
        
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        # dell
        return sh_models.CartItem.objects.get(cart=self.cart, product_id=product.id).delete()

    def __iter_old_(self):
        product_ids = self.cart.keys()
        products = pro_models.Product.objects.filter(id__in=product_ids)
        for product in products:
            self.cart[str(product.id)]['product'] = product

        for item in self.cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        # return sum(item['quantity'] for item in self.cart.values())
        return self.cart.sum_items()

    def get_total_price_(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear_session(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def count(self):
        result = 0
        for item in self.cart.item_set.all():
            result += 1 * item.quantity
        return result

    def summary(self):
        result = 0
        for item in self.cart.item_set.all():
            result += item.total_price
        return result

    def clear(self):
        self.clear_session() 
        for item in self.cart.item_articles.all():
            item.delete()

    def is_empty(self):
        return self.count() == 0

    def cart_serializable(self):
        representation = {}
        for item in self.cart.item_set.all():
            itemID = str(item.product_id)
            itemToDict = {
                'total_price': item.total_price,
                'quantity': item.quantity
            }
            representation[itemID] = itemToDict
        return representation
