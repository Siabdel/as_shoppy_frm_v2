
from django.urls import path
from immoshopy import views 
from project import views as pro_views

app_name = 'immoshop'

urlpatterns = [
    ## Create
    path('', views.home_page, name='home'),
    path('search/', views.search, name='search'),
    path('project/<slug:slug>/', pro_views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/', views.ImmoDetailView.as_view(), name='product_immo_detail'),
    path('product/<slug:slug>/', pro_views.ProjectDetailView.as_view(), name='product_detail'),
 
]
urlpatterns2 = [
    path('', views.HomeView.as_view(), name='immoshop_home'),
]
