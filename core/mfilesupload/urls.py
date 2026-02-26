from django.urls import path
from . import views

urlpatterns = [
    path('list', views.index, name = 'index'),
    path('upload', views.fileupload, name = "File_Uploads")
]