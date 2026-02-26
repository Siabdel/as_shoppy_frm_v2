from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from project import models as proj_models
from django.conf import settings

@method_decorator(login_required(login_url="/admin/login"), 'dispatch')
class ProjectListView(ListView):
    template_name = "project/project_list.html"
    model = proj_models.Project
    context_object_name = "projects"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:

        context =  super().get_context_data(**kwargs)
        context.update ( 
            {
                'app_name' : settings.APP_LABEL.lower(),
            })
        return context
      

@method_decorator(login_required(login_url="/admin/login"), 'dispatch')
class ProjectDetailView(DetailView):
    template_name = "project/project_detail.html"
    model = proj_models.Project
    context_object_name = "project"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:

        context =  super().get_context_data(**kwargs)

        project = self.get_object()
        produits = project.product_set.all()
        project_images = project.images.all()
        ## raise(Exception(project_images))
    
        context.update ( 
            {
            'project_images' : project_images,
            'products' : produits,
            'image' : project_images.first(),
            'app_name' : "carshop",
            })
      
        return context
    
    

