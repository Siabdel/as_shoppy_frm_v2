from django import forms
from django.forms import ModelForm
from .models import Customer, Invoice, InvoiceItem
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem

class InvoiceItemsForm(ModelForm):
    class Meta:
        model = InvoiceItem
        fields = "__all__"


class InvoiceCreateForm(ModelForm):
    class Meta:
        model = Invoice
        fields = ["client"]

    def __init__(self, *args, **kwargs):
        #user = kwargs.pop("user")
        super(InvoiceCreateForm, self).__init__(*args, **kwargs)
        #self.fields["client"].queryset = Customer.objects.filter(user=user)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['id', 'client', 'status', 'expiration_date']
        

InvoiceItemFormSet = inlineformset_factory(
    Invoice, 
    InvoiceItem, 
    #fields = ['invoice', 'quantity', 'price'],
    fields = ['product', 'quantity', 'price', 'rate', 'tax'],
    extra=0,
    can_delete=True
)
