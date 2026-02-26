from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (CreateView, ListView, 
                                  DetailView, UpdateView, DeleteView)

from django.shortcuts import render, redirect
from django.urls import reverse, resolve
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from customer.forms import AccountUserCreationForm
from customer.forms import UserChangeForm 
from django.db import transaction   
from shop.models import ShopCart
from django.conf import settings
from shop import models as sh_models
from customer import models as cli_models
from customer.forms import ClientCreateForm
from invoice.views import create_invoice
from invoice import models as inv_models


@method_decorator(login_required(login_url="/admin/login"), 'dispatch')
class CustomCreate(CreateView):
    template_name = "customer/create_account_vuejs.html"
    form_class = AccountUserCreationForm
    success_url = '/shop/success/' # we will be redirected to
    
    def get_context_data(self, **kwargs):
        # author = get_object_or_404(User, pk=user_id)
        context = super(CustomCreate, self).get_context_data(**kwargs)

        if self.request.POST:
            context['formset'] = CustomFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['formset'] = CustomFormSet(instance=self.object)
        return context
    
    def form_valid(self, form, formset): 
        # 
        with transaction.atomic():
            self.object = form.save(commit=False) # update username & save form
            self.object.username = self.object.email.split('@')[0]
            form.save()

            if formset.is_valid():
                formset.instance = self.object
                #client = formset.save(commit=False)
                formset.save()
                #
                # create invvoice 
                self.create_invoice(formset[0].cleaned_data)
                
        return super().form_valid(form)
     
    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formset = CustomFormSet(self.request.POST, self.request.FILES)

        # unique user
        v_email = self.request.POST['email']
        queryset =   User.objects.filter(email=v_email)
        """ 
        if  queryset.exists():
            messages.add_message(self.request, messages.INFO,
                             f" user exist ? = { v_email }")
            ##raise Exception("post formser = ", self.request.POST['email'])
            return self.form_invalid(form, formset)
        """

        if form.is_valid() and formset.is_valid():
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)
        
    def form_invalid(self, form, formset):
        context = self.get_context_data(form=form, formset=formset)
        ##context['currentStep'] = 2
        return self.render_to_response(context)
    
    
class SignUp(CreateView):
    form_class = AccountUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = cli_models.Customer
    template_name = "new_client.html"
    form_class = ClientCreateForm

    def get(self, request: HttpRequest, *args: str, **kwargs: reverse_lazy) -> HttpResponse:
        ## voir si le client existe pour ce client 
        return super().get(request, *args, **kwargs)
        
    def form_invalid(self, form):
        response = super().form_invalid(form)
        return response
    
    def form_valid(self, form):
        # set user connecte
        form.instance.user = self.request.user
        client = form.save(commit=False)
        # user correspondant a ce client
        client.created_by = self.request.user
        
        with transaction.atomic():
            client.save()
            # create invoice 
            pdf_response = create_invoice(self.request, client.id)
            #return pdf_response

        ## return super().form_valid(form)
        return redirect(reverse("shop:client_checkout"))


@method_decorator(login_required(login_url="/admin/login"), 'dispatch')
class ClientListView(LoginRequiredMixin, ListView):
    template_name = "client_list.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return cli_models.Customer.objects.filter(created_by=self.request.user)
        else:
            return cli_models.Customer.objects.none()


class ClientDetailView(LoginRequiredMixin, DetailView):
    template_name = "client_detail.html"
    context_object_name = "client"

    def get_object(self):
        client = super().get_object()
        return client
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoices = self.get_invoices_set()
        context.update({"invoices" : invoices})
        return context

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return cli_models.Customer.objects.filter(created_by=self.request.user)
        else:
            return cli_models.Customer.objects.none()

    def get_invoices_set(self):
        if self.request.user.is_authenticated:
            return inv_models.Invoice.objects.filter(client=self.get_object())
        else:
            return inv_models.Invoice.objects.none()



class ClientUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "edit_client.html"
    context_object_name = 'client'
    model = cli_models.Customer
    form_class = ClientCreateForm
    

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return cli_models.Customer.objects.filter(created_by=self.request.user)
        else:
            return cli_models.Customer.objects.none()
        
    def get_success_url(self):
        return reverse_lazy('customer:client-detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "confirm_delete_client.html"
    success_url = reverse_lazy("client-list")

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return cli_models.Customer.objects.filter(created_by=self.request.user)
        else:
            return cli_models.Customer.objects.none()

