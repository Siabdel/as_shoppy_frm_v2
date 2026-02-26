#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file is part of the prometeo project.

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

__author__ = 'Emanuele Bertoldi <emanuele.bertoldi@gmail.com>'
__copyright__ = 'Copyright (c) 2011 Emanuele Bertoldi'
__version__ = '0.0.5'

from django.db import models
#from django.db.models import permalink
from django.conf import settings
from django.urls import reverse, resolve
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey

class Category(models.Model):
    name = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=150, unique=True ,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('name', )
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:product_list_by_category', args=[self.slug])

class MPCategory(MPTTModel):
    """ Category table implement MPTT"""
    name = models.CharField(_('Category Name'), help_text=_('Requird and uniq'), 
                              max_length=150, db_index=True)
    slug = models.SlugField(max_length=150, unique=True ,db_index=True)
    is_active = models.BooleanField(_("Is active"), default=True)
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    class MPTTModel:
        ordering = ('name', )
        ordering_insertion_by = ('name', )
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:product_list_by_category', args=[self.slug])

class Document(models.Model):
    document        = models.FileField(upload_to='documents/')
    do_title           = models.CharField(max_length=255, blank=True, null=True)
    do_description     = models.TextField( blank=True, null=True)
    file_basename   = models.CharField(max_length=50, blank=True, null=True)
    thumbnail_file  = models.CharField(max_length=50, blank=True, null=True)
    file_type       = models.CharField(max_length=20, blank=True, null=True)
    file_size       = models.BigIntegerField(blank=True, null=True)
    initial_name    = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    active  = models.BooleanField()

    def __str__(self):
        return "%s" % (self.do_title)

    def __unicode__(self):
        return "%s" % (self.do_tile)

class GDocument(models.Model):
    document    = models.ForeignKey(Document, null=True, blank=True, verbose_name=_('piece jointe'), on_delete=models.CASCADE)
    created     = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # Listed below are the mandatory fields for a generic relation
    content_type    = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id       = models.PositiveIntegerField()
    content_object  = GenericForeignKey('content_type', 'object_id')


    def __unicode__(self):
        return "%s" % (self.document)


class TaggedItem(models.Model):
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.tag



class Commentaire(models.Model):
   description = models.TextField()
   created     = models.DateTimeField(auto_now_add=True, null=True, blank=True)
   user_assignee      = models.ForeignKey('auth.User', related_name="assigned_comments", on_delete=models.CASCADE)
   current_status     = models.CharField(max_length=20, null=True, blank=True)
   # Listed below are the mandatory fields for a generic relation
   content_type        = models.ForeignKey(ContentType, on_delete=models.CASCADE)
   object_id           = models.PositiveIntegerField()
   content_object      = GenericForeignKey('content_type', 'object_id')


   def __unicode__(self):
       return "%s" % (self.description[:50])


class Result(models.Model):
    """Query result model.
    """
    title = models.CharField(_('title'), max_length=100)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = _('result')
        verbose_name_plural = _('results')

    def get_absolute_url(self):
        try:
            return self.content_object.get_absolute_url()
        except:
            return None

class Tag(models.Model):
    """Tag model.
    """
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), unique=True)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ('title',)

    def __unicode__(self):
        return u'%s' % self.title

    def _occurences(self):
        object_list = []
        related_objects = self._meta.get_all_related_many_to_many_objects()
        for related in related_objects:
            if related.opts.installed:
                model = related.model
                for obj in model.objects.select_related().filter(tags__title=self.title):
                    object_list.append(obj)
        return object_list
    occurences = property(_occurences)

    #@models.permalink
    def get_absolute_url(self):
        return ("tag_detail", (), {"slug": self.slug})

class VoteManager(models.Manager):
    """Custom manager for Vote model.
    """
    def get_for_model(self, m):
        ctype = ContentType.objects.get_for_model(m)
        if isinstance(m, models.Model):
            return self.filter(content_type=ctype, object_id=m.pk)
        return self.filter(content_type=ctype)

    def get_for_models(self, ms):
        qs = Q()
        for m in ms:
            ctype = ContentType.objects.get_for_model(m)
            if isinstance(m, models.Model):
                qs |= Q(content_type=ctype, object_id=m.pk)
            else:
                qs |= Q(content_type=ctype)
        return self.filter(qs)

class Vote(models.Model):
    """Vote model.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    owner = models.ForeignKey('auth.User', related_name='poll_votes', verbose_name=_('owner'), on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('created'))

    objects = VoteManager()

    class Meta:
        verbose_name = _('vote')
        verbose_name_plural = _('votes')
        unique_together = (("owner", "content_type", "object_id"),)
#----------------------