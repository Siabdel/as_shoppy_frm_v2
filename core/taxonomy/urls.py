#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file is part of the
"""

__author__ = 'Abdelaziz Sadquaoui >'
__copyright__ = 'Copyright (c) 2019 strandcosmeticseurope.com'
__version__ = '0.9'

from django.conf.urls import url, include
from django.contrib import admin
from  core.taxonomy import views

app_name="taxonomy"

urlpatterns = [
    # Search.
    url(r'^search/$', views.search, name='search'),
    url(r'^search/(?P<query_string>.+)/$', views.search, name='search_with_query'),

    # Categories.
    url(r'^categories/$', views.category_list, name='category_list'),
    url(r'^categories/add/$', views.category_add, name='category_add'),
    url(r'^categories/(?P<slug>[-\w]+)/$', views.category_detail, name='category_detail'),
    url(r'^categories/(?P<slug>[-\w]+)/edit/$', views.category_edit, name='category_edit'),
    url(r'^categories/(?P<slug>[-\w]+)/delete/$', views.category_delete, name='category_delete'),

    # Tags.
    url(r'^tags/$', views.tag_list, name='tag_list'),
    url(r'^tags/add/$', views.tag_add, name='tag_add'),
    url(r'^tags/(?P<slug>[-\w]+)/$', views.tag_detail, name='tag_detail'),
    url(r'^tags/(?P<slug>[-\w]+)/edit/$', views.tag_edit, name='tag_edit'),
    url(r'^tags/(?P<slug>[-\w]+)/delete/$', views.tag_delete, name='tag_delete'),
]
