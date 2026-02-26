from rest_framework import serializers
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from rest_framework import serializers
from immoshop import models as immo_models


class UserSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = '__all__'
# Document
class DocumentApiSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(many=False, read_only=True)
    # author = UserSerializer()