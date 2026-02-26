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

## from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _


__author__ = 'Emanuele Bertoldi <emanuele.bertoldi@gmail.com>'
__copyright__ = 'Copyright (c) 2011 Emanuele Bertoldi'
__version__ = '0.0.5'


VISIBILITE_CHOICES = [("P" , "Projet Public"), ("I", "Projet interne"), ("C", "Projet lié à un client"),  ("V", "Projet privé seulement au abonnés"),]
VISIBILITE_DEFAULT = "Projet Public"


PROJECT_STATUS_CHOICES = (
    ('OPEN', _('open')),
    ('CLOSED', _('closed')),
)

PROJECT_DEFAULT_STATUS = 'OPEN'

PROJECT_CLOSE_STATUSES = ('CLOSED',)

TICKET_URGENCY_CHOICES = (
    ('FAIBLE',  _('pas important pas urgent')), # Jaune
    ('CRITIQUE', _('important et pas Urgent')), # vert

    ('MOYEN',   _('uregnt et pas importance')),   # Orange
    ('URGENT',  _('Urgent et Important')),       # Urgent et important
)

TICKET_DEFAULT_URGENCY = 'MOYEN'

TICKET_TYPE_CHOICES = (
    ('BUG', _('bug')),
    ('TASK', _('task')),
    ('IDEA', _('idea')),
)

TICKET_DEFAULT_TYPE = 'BUG'

TICKET_STATUS_CHOICES = (
    ('NOUVEAU', _('nouveau')),
    ('ENCOURS', _('encours')),
    ('RESOLUE', _('resolue')),
    ('CLOTUREE', _("cloturee")),
    ('ANNULEE', _('annulee')),
    ('ENATTENTE', _('en attente')),
)

TICKET_DEFAULT_STATUS = 'NOUVEAU'

# TICKET_CLOSE_STATUSES = ('INVALID', 'DUPLICATE', 'RESOLVED')
TICKET_CLOSE_STATUSES = ('CLOTUREE', 'ANNULEE', )

## TASKS



TASK_URGENCY_CHOICES_OLD = (
    ('TRES FAIBLE', _('tres faible importance')),
    ('FAIBLE', _('faible importance')),
    ('MOYEN', _('moyen importance')),
    ('FORT', _('fort')),
    ('CRITIQUE', _('critique')),
)

"""Dans la gestion de projet agile, cette méthode de priorisation
se concentre justement sur l’importance de la tâche et son impact
 sur la réalisation du projet
"""
TASK_URGENCY_CHOICES = (
    ('OPTIONNELLE', _('optionnelle')),
    ('FAIBLE', _('faible importance')),
    ('IMPORTANT', _('important')),
    ('URGENT', _('fort importance')),
)

TASK_DEFAULT_URGENCY = 'MOYEN'

TASK_TYPE_CHOICES = (
    ('ACTION', _('action')),
    ('TASK', _('task')),
    ('IDEE', _('idee')),
)

TASK_DEFAULT_TYPE = 'ACTION'

TASK_STATUS_CHOICES = (
    ('NOUVEAU', _('nouveau')),
    ('ENCOURS', _('encours')),
    ('TERMINEE', _('terminee')),
    ('CLOTUREE', _("cloturee")),
    ('ANNULEE', _('annulee')),
    ('ENATTENTE', _('en attente')),
)

TASK_DEFAULT_STATUS = 'NOUVEAU'

TASK_CLOSE_STATUSES = ('INVALIDE', 'DUPLIQUEE', 'RESOLUE')
