from django.urls import path

from . import views
from .api_views import (
    InvoiceListView, InvoiceDetailView,
    InvoiceItemListView, InvoiceItemDetailView
)

app_name = "invoice"

urlpatterns = [
    path("new/<int:customer_id>", views.create_invoice, name="new-invoice"),
    path( "invoice/<customer_id>", views.create_invoice, name="create-invoice",),
    path("list/", views.InvoiceListView.as_view(), name="invoice-home"),
    path("<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice-detail"),
    path( "edit/<int:pk>/", views.InvoiceUpdateView.as_view(), name="invoice-edit",),
    path( "pdf/<invoice_id>", views.generate_pdf_invoice, name="generate-pdf",),
]