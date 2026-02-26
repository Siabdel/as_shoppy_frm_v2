from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ProjectViewSet, TaskViewSet, TicketViewSet
from project import views

app_name = "project"

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'tickets', TicketViewSet)

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('catalog/', views.ProjectListView.as_view(), name='project_catalog'),
    path('<int:pk>', views.ProjectDetailView.as_view(), name='project_detail'),
]

urlpatterns += [
    path('api/', include(router.urls)),
]
