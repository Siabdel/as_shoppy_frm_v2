#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.apps import apps
class Dict2Obj(object):
    """
    Turns a dictionary into a class
    """
    #----------------------------------------------------------------------
    def __init__(self, dictionary):
        """Constructor"""
        for key in dictionary:
            setattr(self, key, dictionary[key])

class DependencyError(Exception):
    def __init__(self, app_name):
        self._app_name = app_name

    def __str__(self):
        return u"A dependency is not satisfied: %s" % app_name

def check_dependency(app_name):
    if app_name not in settings.INSTALLED_APPS:
        raise DependencyError(app_name)

def clean_referer(request, default_referer='/'):
    """Returns the HTTP referer of the given <request>.

    If the HTTP referer is not recognizable, <default_referer> is returned.
    """
    referer = request.META.get('HTTP_REFERER', default_referer)
    return referer.replace("http://", "").replace("https://", "").replace(request.META['HTTP_HOST'], "")



def make_thumbnail(image, size=(100, 100)):
    """Makes thumbnails of given size from given image"""

    im = Image.open(image)

    im.convert('RGB') # convert mode

    im.thumbnail(size) # resize image

    thumb_io = BytesIO() # create a BytesIO object

    im.save(thumb_io, 'JPEG', quality=85) # save image to BytesIO object

    thumbnail = File(thumb_io, name=image.name) # create a django friendly File object

    return thumbnail

##  
def get_product_model():
    product_model_string = getattr(settings, 'CART_PRODUCT_MODEL', "Product")
    nb = len(product_model_string.split('.'))

    if nb == 2:
        app_label, model_name = product_model_string.split('.')
    elif nb == 3 :
        core, app_label, model_name = product_model_string.split('.')

    model = apps.get_model(app_label, model_name)
    if model is None:
        raise LookupError(f"App '{app_label}' doesn't have a '{model_name}' model.")
    return model
def process_resize_image(image, output_dir, thumbnail_size=(100, 100), large_size=(800, 600)):
    """
    Traite une images de produit en créant des miniatures de taille uniforme
    et une grande image.

    Args:
        image :  ProductImage instance
        output_dir (str): Le répertoire de sortie où les images traitées seront enregistrées.
        thumbnail_size (tuple): Taille de la miniature (largeur, hauteur). Par défaut: (100, 100).
        large_size (tuple): Taille de la grande image (largeur, hauteur). Par défaut: (800, 600).
    """

    # Ouvre l'image
    with Image.open(image.image.path) as img:
        # Crée une miniature
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size)

        # Crée une grande image avec un rapport d'aspect préservé
        large_img = img.copy()
        
        # Size of the image in pixels (size of original image) 
        # (This is not mandatory) 
        width, height = large_img.size 
 
       
        # Enregistre les images traitées
        base_name = os.path.basename(image.image.path)
        thumbnail_path = os.path.join(output_dir, 
                                  f"thumbnail_{thumbnail_size[0]}x{thumbnail_size[1]}_{base_name}")
        large_path = os.path.join(output_dir,
                                  f"large_{large_size[0]}x{large_size[1]}_{base_name}")

        thumbnail.save(thumbnail_path)
        #large_img.save(large_path)
        large_img.save(large_path)

        # Retourne les chemins des images traitées
        return thumbnail_path, large_path


def process_default_image(image, output_dir, thumbnail_size=(100, 100), large_size=(800, 600)):
    """
    """
    # Ouvre l'image
    with Image.open(image.path) as img:
        # Crée une miniature
        thumbnail = img.copy()
        thumbnail.thumbnail(thumbnail_size)

        # Crée une grande image avec un rapport d'aspect préservé
        large_img = img.copy()
        large_img.thumbnail(large_size)

        # Enregistre les images traitées
        base_name = os.path.basename(image.path)
        thumbnail_path = os.path.join(output_dir, f"thumbnail_{base_name}")
        large_path = os.path.join(output_dir, f"large_{base_name}")

        thumbnail.save(thumbnail_path)
        large_img.save(large_path)

        # Retourne les chemins des images traitées
        return thumbnail_path, large_path
