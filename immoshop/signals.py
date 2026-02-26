  
# 
import os
from django.db.models.signals import post_save, pre_delete,pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from product.models import ImmoProduct, ImmoProductImage
from core.utils import process_resize_image, process_default_image
from django.conf import settings

@receiver(post_save, sender=ImmoProduct, )
def post_product_create(sender, instance, created, **kwargs):
    output_dir = os.path.join(settings.MEDIA_ROOT, "images")

    if  created:
        #ImmoProductinstance.default_image.objects.create(product=instance)
        image = instance.default_image.instance.default_image
        # raise Exception(f" { produit.default_image.url  }  ")
        thumbnail_path, large_path = process_default_image(instance.default_image, output_dir)
        #raise Exception(f"alert un produit est creer ou save {instance} !!!")
    
 
