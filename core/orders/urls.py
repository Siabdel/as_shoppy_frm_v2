from django.urls import path
from . import views

app_name = 'orders'

# Abstract models cannot be used directly - views should be provided by business-specific apps
# The order_create view requires a concrete Order model with the appropriate fields

urlpatterns = [
    # path('create/', views.order_create, name='order_create')
]