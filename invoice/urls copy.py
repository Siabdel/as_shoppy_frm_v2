from django.urls import path

from . import views
from .api_views import (
    InvoiceListView, InvoiceDetailView,
    InvoiceItemListView, InvoiceItemDetailView
)

app_name = "invoices"

urlpatterns = [
    path("", views.HomePage.as_view(), name="home"),
    # Invoices
    path("list/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("new/", views.InvoiceCreateView.as_view(), name="new-invoice"),
    path( "<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path( "edit/<int:pk>/", views.InvoiceUpdateView.as_view(), name="invoice-edit",),
    path( "delete/<int:pk>/", views.InvoiceDeleteView.as_view(), name="invoice-delete",),
    path( "delete/<int:pk>/", views.InvoiceDeleteView.as_view(), name="invoice-delete",),
    path( "generate/<invoice_id>", views.generate_pdf_invoice, name="generate_pdf",),
    path("upload/", views.simple_upload, name="upload"),
]
#---------
# API's
#---------
urlpatterns += [
    path('api/v1/invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('api/v1/invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('api/v1/invoice-items/', InvoiceItemListView.as_view(), name='invoice-item-list'),
    path('api/v1/invoice-items/<int:pk>/', InvoiceItemDetailView.as_view(), name='invoice-item-detail'),
]
