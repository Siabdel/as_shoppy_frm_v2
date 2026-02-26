
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import Quote

from django import forms
from django.forms import inlineformset_factory
from .models import Quote, QuoteItem
from customer.models import Customer


class QuoteItemForm(forms.ModelForm):
    class Meta:
        model = QuoteItem
        fields = ['product', 'quantity', 'price', 'rate', 'tax']
        widgets = {
            'product': forms.Select(attrs={'class': 'select2'}),
            'client': forms.Select(attrs={'class': 'select2'}),
        }

QuoteItemFormSet = inlineformset_factory(
    Quote, QuoteItem,
    form=QuoteItemForm,
    extra=1,
    can_delete=True
)
class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['client', 'date_expiration', 'total_amount', 'status', 'quote_terms']
        widgets = {
            'date_expiration': forms.DateInput(attrs={'type': 'date'}),
        }


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(QuoteForm, self).__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            self.fields['client'].queryset = Customer.objects.filter(created_by=self.user)
          # Formater la date d'expiration pour le widget date HTML5
        if self.instance.date_expiration:
            self.initial['expiration_date'] = self.instance.date_expiration.strftime('%Y-%m-%d')

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('client', css_class='form-group col-md-6 mb-0'),
                Column('date_expiration', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('total_amount', css_class='form-group col-md-6 mb-0'),
                Column('status', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'quote_terms',
            Submit('submit', 'Enregistrer', css_class='btn btn-primary')
        )

    def clean_total_amount(self):
        montant = self.cleaned_data['total_amount']
        if montant <= 0:
            raise forms.ValidationError("Le montant total doit être supérieur à zéro.")
        return montant