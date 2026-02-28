from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import api_views
import os

app_name = 'customer'

# Dashboard view (simple function-based view)
def dashboard_view(request):
    from django.shortcuts import render
    return render(request, 'customer/dashboard_cmagic.html')

urlpatterns = [
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name='customer/login.html'), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='/'), name="logout"),
    ## Create
    path('create_client/', views.ClientCreateView.as_view(), name='client-create'),
     # Clients
    path("list/", views.ClientListView.as_view(), name="client-list"),
    path("<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("edit/<int:pk>/", views.ClientUpdateView.as_view(), name="client-edit"),
    path("del/<int:pk>/", views.ClientDeleteView.as_view(), name="client-delete"),
    # Dashboard
    path("dashboard/", dashboard_view, name="dashboard"),
]


