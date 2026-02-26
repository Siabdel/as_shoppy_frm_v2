# models.py
from typing import Any, MutableMapping
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _
from product import models as pro_models

class ImmoProduct(pro_models.Product):
    
    def get_images(self):
        return self.images.all()

    def get_absolute_url(self):
        return reverse("immoshop:product_immo_detail", args=[str(self.id)])

class ImmoProductImage(pro_models.ProductImage):
    pass
    
class ImmoProductSpecificationValue(pro_models.ProductSpecificationValue):
    """ The product specification value table hold each of the 
    product individal specification or bespoke features.
    """
    pass