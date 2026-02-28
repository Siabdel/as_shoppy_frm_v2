# -*- coding: utf-8 -*-
"""
Template tags pour le panier cmagic_sport
"""
from django import template

register = template.Library()


@register.simple_tag
def get_cart_items_count(request):
    """
    Retourne le nombre d'articles dans le panier.
    Utilise le contexte 'cart' fourni par core.context_processors.shop
    """
    cart = getattr(request, 'cart', None)
    if cart and hasattr(cart, 'num_items'):
        return cart.num_items
    return 0


@register.simple_tag
def get_cart_total(request):
    """
    Retourne le total du panier.
    """
    cart = getattr(request, 'cart', None)
    if cart and hasattr(cart, 'total'):
        return cart.total
    return 0
