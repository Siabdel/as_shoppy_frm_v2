"""
Customer Serializers

Django REST Framework serializers for the customer API.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Customer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (nested in Customer)."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']


class CustomerSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer model.
    
    Provides full customer details including user information.
    """
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    order_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'user_id', 'state', 'state_display',
            'recognized', 'created_at', 'updated_at', 'last_access',
            'extra', 'order_count'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_access']
    
    def get_order_count(self, obj):
        """Return the number of orders for this customer."""
        return obj.orders.count()
    
    def create(self, validated_data):
        """Create a new customer."""
        return Customer.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing customer."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for customer list views.
    
    Provides essential information for list displays.
    """
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'username', 'email', 'full_name',
            'state', 'state_display', 'recognized', 'created_at'
        ]
    
    def get_full_name(self, obj):
        """Return the user's full name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return ""


class CustomerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new customers with user account.
    """
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'username', 'email', 'password',
            'first_name', 'last_name', 'state', 'extra'
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """Create user and associated customer."""
        user_data = {
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'first_name': validated_data.pop('first_name', ''),
            'last_name': validated_data.pop('last_name', ''),
        }
        password = validated_data.pop('password')
        
        user = User.objects.create_user(password=password, **user_data)
        customer = Customer.objects.create(user=user, **validated_data)
        return customer
