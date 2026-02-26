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

from django.contrib import admin
from django.contrib.auth.models import Permission

import core.profile.models as profile_models

class PermissionAdmin(admin.ModelAdmin):
    pass

class ObjectPermissionAdmin(admin.ModelAdmin):
    pass

admin.site.register(profile_models.Permission, PermissionAdmin)
admin.site.register(profile_models.ObjectPermission, ObjectPermissionAdmin)


class SocieteAdmin(admin.ModelAdmin) :
    list_total = [ f.name for f in  profile_models.Societe._meta.get_fields() ]
    search_fields = ['name', ]
    list_total.remove( 'parent', )
    list_display = ( 'name', 'parent', 'description', )




class FonctionAdmin(admin.ModelAdmin) :
    list_total  = [ f.name for f in  profile_models.Fonction._meta.get_fields() ]
    list_total.remove('uprofile', )
    search_fields = ['name', ]
    list_display = list_total

class ServiceAdmin(admin.ModelAdmin) :
    list_total  = [ f.name for f in  profile_models.Service._meta.get_fields() ]
    search_fields = ['name', 'societe', ]
    list_total.remove('uprofile', )
    list_display = list_total

#registre
admin.site.register(profile_models.Societe, SocieteAdmin)
admin.site.register(profile_models.Service, ServiceAdmin)
admin.site.register(profile_models.Fonction, FonctionAdmin)
