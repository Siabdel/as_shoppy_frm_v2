#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file
This program is appli todo for manage projects
"""

__author__ = 'Abdelaziz Sadquaoui'
__copyright__ = 'Copyright (c) 2019 Strand Cosmetics'
__version__ = '0.9'

from django.db import models
from django.contrib.auth.models import User, Group, Permission
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.template.defaultfilters import slugify
from django.utils.text import slugify
# from managers import MyPermissionManager

# from managers import *

class Societe(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children',  on_delete=models.SET_NULL)
    name         = models.CharField(max_length=255, blank=True, null=True)
    description  = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('name', )

    def __str__(self):
        return self.name

class Fonction(models.Model):
    slug = models.SlugField(default='', editable=False,)
    name = models.CharField(verbose_name="Nom de la fonction", max_length=200)

    class Meta:
        unique_together = ('name', )

    def __unicode__(self):
        return "{}".format(self.name)

    def save(self, *args, **kwargs):
            value = self.name
            self.slug = slugify(value, allow_unicode=True)
            super(Fonction, self).save(*args, **kwargs)

class Service(models.Model):
    societe = models.ForeignKey(Societe, blank=True, null=True, verbose_name=_("Societe"), on_delete=models.SET_NULL)
    slug = models.SlugField(default='', editable=False,)
    name = models.CharField(verbose_name="Nom du service", max_length=200)

    class Meta:
        #unique_together = ('societe', 'slug' )
        verbose_name = _('Services de la societe')


    def __unicode__(self):
        return "{}".format(self.name)

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super(Service, self).save(*args, **kwargs)

ROLE_CHOICES = (
        (1, 'Manager'),
        (2, 'Superviseur'),
        (3, 'Utilisateur'),
    )


class UProfile(models.Model):
    # User profile.
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    following = models.ManyToManyField(User, related_name='followers', blank=True)
    language = models.CharField(max_length=5, null=True, choices=[(settings.LANGUAGES, settings.LANGUAGES)], default=settings.LANGUAGE_CODE, verbose_name=_("language"))
    timezone = models.CharField(max_length=20, null=True, choices=[(settings.TIME_ZONE, settings.TIME_ZONE)],  default=settings.TIME_ZONE, verbose_name=_("timezone"))
    # dashboard = models.OneToOneField('widgets.Region', null=True, verbose_name=_("dashboard"))
    # bookmarks = models.OneToOneField('menus.Menu', null=True, verbose_name=_("bookmarks"))
    # calendar = models.OneToOneField('calendar.Calendar', null=True, verbose_name=_("calendar"))
    date_naissance = models.DateField(verbose_name="Date de naissance", null=True, blank=True)
    photo = models.FileField(upload_to='documents/', null=True, blank=True)
    #societe = models.ForeignKey('Societe', null=True, blank=True)
    fonction = models.ForeignKey('Fonction', null=True, blank=True, on_delete=models.SET_NULL)
    service = models.ForeignKey('Service', null=True, blank=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=25, null=True, choices=[(1, settings.LANGUAGES)], default=settings.LANGUAGE_CODE, verbose_name=_("language"))
    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=3)



    @property
    def full_name(self):
        if self.user.first_name :
            return u"{} {}".format(self.user.first_name, self.user.last_name)
        else :
            return u"{}".format(self.user.username)

    def __unicode__(self): # __unicode__ for Python 2
        return "{} {}".format(self.user.first_name, self.user.last_name)

    def get_language(self):
        return self.language

    def get_timezone(self):
        return self.timezone

    #@receiver(post_save, sender=User)
    def create_or_update_user_profile(sender, instance, created, **kwargs):
        if created:
            UProfile.objects.create(user=instance)
        #instance.profile.save()



class ObjectPermission(models.Model):
    """A generic object/row-level permission.
    """
    object_id = models.PositiveIntegerField()
    perm = models.ForeignKey(Permission, verbose_name=_("permission"), on_delete=models.CASCADE)
    users = models.ManyToManyField(User,   blank=True, related_name='objectpermissions', verbose_name=_("users"))
    groups = models.ManyToManyField(Group,  blank=True, related_name='objectpermissions', verbose_name=_("groups"))

    # objects = ObjectPermissionManager()

    class Meta:
        verbose_name = _('object permission')
        verbose_name_plural = _('object permissions')

    def __unicode__(self):
        return "%s | %d" % (self.perm, self.object_id)


"""
class MyPermission(Permission):
    # A Project's permission.

    class Meta:
        proxy = True

    objects = MyPermissionManager()
"""
