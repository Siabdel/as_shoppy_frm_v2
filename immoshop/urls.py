from django.urls import path
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from weasyprint import HTML
from shop import views as shop_models 
from immoshop import api as shop_apiviews
from immoshop import api as shop_api
from immoshop import views as immo_views


app_name="immoshop"

urlpatterns = [
    #path('home/', shop_models.product_immo_list, name='home_immo_list'),
    path('', shop_models.product_home, name='home_immo_list'),
    path('home/', shop_models.product_home, name='home_immo_list'),
    path('list/', shop_models.product_home, name='product_immo_list'),
    path('cat/<slug:category_slug>/', shop_models.product_immo_list, name='product_list_by_category'),
    path('show/<int:pk>/', shop_models.ProductDetailView.as_view(), name='product_immo_detail'),
    # Devis invoice
    path('create_invoice/<int:user_id>', immo_views.InvoiceCreate.as_view(), name='invoice_create'),
    path('invoices/generate/<int:invoice_id>', immo_views.generate_pdf_invoice, name="generate_pdf",),
    ## successs
    path('success/', immo_views.success, name="success",),
    ## API 
    path('api/user/', shop_apiviews.UserApiList.as_view(), name="user_api" ), # new
    path('api/user/<int:pk>/', shop_apiviews.UserApiDetail.as_view(), name="user_api" ), # new
]