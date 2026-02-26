# models.py
from django.db import models
from typing import Any, MutableMapping
from django.urls import reverse
from django.utils.translation import gettext as _
from product import models as pro_models

# Create your models here.
class VehiculeProduct(pro_models.Product):
    couleur = models.CharField(max_length=100)

    def get_images(self):
        return self.images.all()

    def get_absolute_url(self):
        return reverse("carshop:product_car_detail", args=[str(self.id)])

    def __str__(self):
        return super().__str__()
class CarProductImage(pro_models.ProductImage):
    pass

    def __str__(self):
        return super().__str__()
    
class CarProductSpecificationValue(pro_models.ProductSpecificationValue):
    """ The product specification value table hold each of the 
    product individal specification or bespoke features.
    """
    pass