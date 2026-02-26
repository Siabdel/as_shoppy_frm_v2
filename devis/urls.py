
from django.urls import path, include
from devis import views
from rest_framework.routers import DefaultRouter
from .api_views import QuoteViewSet, QuoteItemViewSet

app_name = 'quote'  # Ceci est utile pour le nommage des URL

router = DefaultRouter()
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'quote-items', QuoteItemViewSet, basename='quote-item')

urlpatterns = [
    # Liste des devis
    path('', views.QuoteListView.as_view(), name='quote_list'),
    
    # Détails d'un devis
    path('<int:pk>/', views.QuoteDetailView.as_view(), name='quote_detail'),
    
    # Création d'un nouveau devis
    path('create/', views.QuoteCreateView.as_view(), name='quote_create'),
    
    # Mise à jour d'un devis
    path('<int:pk>/update/', views.QuoteUpdateView.as_view(), name='quote_update'),
    
    # Suppression d'un devis
    path('<int:pk>/delete/', views.QuoteDeleteView.as_view(), name='quote_delete'),
    
    # Conversion d'un devis en facture
    path('<int:pk>/convert/', views.convert_quote_to_invoice, name='convert_quote_to_invoice'),
]


urlpatterns += [
    path('api/', include(router.urls)),
    # ... vos autres URL patterns ...
]