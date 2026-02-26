from django.db import models
from product import models as pro_models
from core.base_product import models as base_models

# Create your models here.

#class ImmoProduct(base_models.BaseProduct):
class ImmoProduct(pro_models.Product):
    pass