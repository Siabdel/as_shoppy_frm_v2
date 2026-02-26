from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import Quote, QuoteItem
from .forms import QuoteForm, QuoteItemFormSet
from django.db import transaction 


class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = 'quote/quote_list.html'
    context_object_name = 'quotes'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Quote.objects.all()
        elif hasattr(user, 'customer'):
            return Quote.objects.filter(client=user.customer)
        else:
            return Quote.objects.filter(created_by=user)
    
class QuoteDetailView(LoginRequiredMixin, DetailView):
    model = Quote
    template_name = 'quote/quote_detail.html'
    context_object_name = 'quote'


class QuoteUpdateView(LoginRequiredMixin, UpdateView):
    model = Quote
    form_class = QuoteForm
    template_name = 'quote/quote_form.html'
    success_url = reverse_lazy('quote:quote_list')

    def form_valid(self, form):
        messages.success(self.request, "Le devis a été mis à jour avec succès.")
        return super().form_valid(form)

class QuoteDeleteView(LoginRequiredMixin, DeleteView):
    model = Quote
    template_name = 'quote/quote_confirm_delete.html'
    success_url = reverse_lazy('quote:quote_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Le devis a été supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

def convert_quote_to_invoice(request, pk):
    quote = get_object_or_404(Quote, pk=pk)
    if quote.statut == StatutDevis.ACCEPTE.code:
        invoice = quote.convertir_en_facture()
        messages.success(request, f"Le devis {quote.numero} a été converti en facture {invoice.numero}.")
        return redirect('invoice_detail', pk=invoice.pk)
    else:
        messages.error(request, "Seuls les devis acceptés peuvent être convertis en factures.")
        return redirect('quote_detail', pk=quote.pk)


class QuoteCreateView(LoginRequiredMixin, CreateView):
    model = Quote
    form_class = QuoteForm
    template_name = 'quote/quote_form.html'
    success_url = reverse_lazy('quote:quote_list')

    def get_form_kwargs(self):
        kwargs = super(QuoteCreateView, self).get_form_kwargs()
        kwargs.update({'user':self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(QuoteCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = QuoteItemFormSet(self.request.POST)
        else:
            data['items'] = QuoteItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super(QuoteCreateView, self).form_valid(form)

# create Devis a partir QuoteItem
# Créer des QuoteItems basés sur le contenu du panier
class QuoteCreateView2(LoginRequiredMixin, CreateView):
    model = Quote
    form_class = QuoteForm
    template_name = 'quotes/quote_form.html'
    success_url = reverse_lazy('quote_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        quote = form.save()
        
        # Récupérer le panier de l'utilisateur
        cart = self.request.user.cart
        
        # Créer des QuoteItems basés sur le contenu du panier
        for cart_item in cart.items.all():
            QuoteItem.objects.create(
                quote=quote,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Calculer le total du devis
        quote.total = sum(item.price * item.quantity for item in quote.items.all())
        quote.save()
        
        # Vider le panier après la création du devis
        cart.items.all().delete()
        
        return super().form_valid(form)