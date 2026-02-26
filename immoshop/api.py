# -*- coding:UTF-8 -*-
from __future__ import unicode_literals
import os, sys
import datetime
from django.utils import timezone
from django.db.models.query import QuerySet
import pytz
import json
from django.core import serializers
import  rest_framework
from rest_framework.views import APIView
from django.shortcuts import render
from django.conf import settings
from django.views.generic import ListView, TemplateView
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from immoshop import models as immo_models
from immoshop import serializers as immo_seriz
from django.contrib.auth.models import User


# Residence
class UserApiList(generics.ListCreateAPIView):
    serializer_class = immo_seriz.UserSerializer 
    queryset = User.objects.all().order_by('username')


class UserApiDetail(generics.RetrieveUpdateAPIView):
    serializer_class = immo_seriz.UserSerializer 
    queryset = User.objects.all().order_by('username')
