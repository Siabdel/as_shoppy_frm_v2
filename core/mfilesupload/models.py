from django.db import models

# Create your models here.

from django.db import models

class Image(models.Model):
    pic = models.FileField(upload_to='upload/MFU_Images')