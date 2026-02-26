from django.urls import path
from . import views 
from . import api_views 

app_name = 'customer'

urlpatterns = [
    path("signup/", views.SignUp.as_view(), name="signup"),
    ## Create
    path('create_account/', views.CustomCreate.as_view(), name='account_create'),
    path('create_client/', views.ClientCreateView.as_view(), name='client_create'),
     # Clients
    path("clients/", views.ClientListView.as_view(), name="client-list"),
    path("clients/new/", views.ClientCreateView.as_view(), name="new-client"),
    path("clients/<int:pk>/", views.ClientDetailView.as_view(), name="client-detail"),
    path("clients/edit/<int:pk>/", views.ClientUpdateView.as_view(), name="client-edit"),
    path("clients/delete/<int:pk>/", views.ClientDeleteView.as_view(), name="client-delete",),
]

#---------
# API's
#---------
urlpatterns += [
    path('api/v1/clients/', api_views.ClientListView.as_view(), name='client-list'),
    path('api/v1/clients/<int:pk>/', api_views.ClientDetailView.as_view(), name='client-detail'),
]


