
# views.py
from rest_framework import generics
from .models import Customer, Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceItemSerializer

class InvoiceListView(generics.ListCreateAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer

class InvoiceItemListView(generics.ListCreateAPIView):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer

class InvoiceItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
