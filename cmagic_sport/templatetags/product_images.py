# -*- coding: utf-8 -*-
"""
Template tags pour les images de produits CMagic Sport.
"""
import os
import glob
from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def product_image_url(product, fallback=True):
    """
    Retourne l'URL de l'image du produit.
    Si default_image n'existe pas, cherche dans static/product_images/cmagic_sport/
    
    Usage: {% product_image_url product %}
    """
    # 1. Essayer default_image
    if product.default_image:
        return product.default_image.url
    
    # 2. Chercher dans les fichiers statiques
    if fallback:
        static_dir = os.path.join(
            settings.BASE_DIR,
            'static',
            'product_images',
            'cmagic_sport'
        )
        
        # Chercher tous les fichiers qui commencent par le slug
        pattern = os.path.join(static_dir, f'{product.slug}*.jpg')
        matches = glob.glob(pattern)
        
        if matches:
            # Retourner le premier fichier trouvé
            filename = os.path.basename(matches[0])
            return f'/static/product_images/cmagic_sport/{filename}'
    
    return None


@register.simple_tag
def product_image_fallback(product):
    """
    Retourne l'URL de l'image avec fallback.
    Retourne un tuple (image_url, has_fallback)
    
    Usage: {% product_image_fallback product as img_data %}
           {{ img_url }} ou {{ has_fallback }}
    """
    url = product_image_url(product, fallback=True)
    return url if url else None