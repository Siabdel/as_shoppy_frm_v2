from django import forms

# Abstract models cannot be used directly in forms
# They should be extended by business-specific apps that provide concrete implementations

# from .models import BaseOrderModel as Order


# class OrderCreateForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = ['first_name', 'last_name', 'email', 'address', 'postal_code', 'city']

