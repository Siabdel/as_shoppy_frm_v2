from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.forms.models import inlineformset_factory
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.http import (
    HttpRequest, HttpResponse,
    HttpResponse, HttpResponseRedirect
)
from django.shortcuts import render, redirect

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from weasyprint import HTML
from django.dispatch import Signal
from .forms import InvoiceCreateForm
from .models import Invoice, InvoiceItem
from django.contrib import messages
from shop import models as sh_models
from customer import models as cli_models
from .forms import InvoiceForm, InvoiceItemFormSet

class InvoiceListView(LoginRequiredMixin, ListView):
    template_name = "dashboard.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            invoices = Invoice.objects.all()
            return invoices
        else:
            return Invoice.objects.none()


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    template_name = "invoice_detail.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Invoice.objects.filter(created_by=self.request.user)
        else:
            return Invoice.objects.none()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the data
        context = super(InvoiceDetailView, self).get_context_data(**kwargs)
        # Add client to the context -- to be used by invoice template
        client = context["invoice"].client
        context["client"] = client
        # Add invoice items queryset
        context["invoice_items"] = context["invoice"].items.all()
        created_by = context["invoice"].created_by
        context["created_by"] = created_by
        return context


class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    # fields = ["title", "client", "invoice_terms"]
    template_name = "edit_invoice.html"
    form_class = InvoiceForm

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Invoice.objects.filter(created_by=self.request.user)
        else:
            return Invoice.objects.none()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data["invoice_items"] = InvoiceItemFormSet(
                self.request.POST, instance=self.object
            )
        else:
            data["invoice_items"] = InvoiceItemFormSet(instance=self.object)
        return data
    
    def post(self, request: HttpRequest, *args: str, **kwargs: reverse_lazy): 
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            items = formset.save(commit=False)
            for item in items:
                item.invoice = invoice
                item.save()
            return redirect('invoice:invoice_list')
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        context = self.get_context_data()
        invoice_items = context["invoice_items"]
        self.object = form.save()
        if invoice_items.is_valid():
            invoice_items.instance = self.object
            invoice_items.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("invoice:invoice-detail", args=[self.object.pk])



@login_required
def create_invoice(request, customer_id): 
    # cart 
    cart = sh_models.ShopCart.objects.get(created_by=request.user)
    # if cart empty go to catalog
    if cart.items.all().count() == 0 : 
        return redirect("project:project_detail", 1)
    # 1- create invoice + ItemInvoice
    client = cli_models.Customer.objects.get(id=customer_id)
    #raise Exception("create invoice = ", cart.items.all().count(), client.id)
    invoice = convert_cart_to_invoice(cart, client)

    # Emit the signal when checkout is complete
    # This could be in your view or wherever the checkout process finishes
    # Empty Cart
    #checkout_completed.send(sender=Invoice, user=request.user)
    # create pdf 
    return generate_pdf_invoice(request, invoice.id)

            
def convert_cart_to_invoice(shop_cart, customer):
    #raise Exception("create invoice = ", customer.id)
    invoice = Invoice.objects.create(created_by=shop_cart.created_by, 
                                        client=customer,
                                        total_amount=0)
    total_amount = 0
    for item in shop_cart.items.all():
        product = item.product
        invoice_item = InvoiceItem.objects.create(
            invoice=invoice,
            product=product,
            quantity=item.quantity,
            price=item.product.price
        )
        # save 
        invoice_item.save()
        total_amount += product.price * item.quantity

    invoice.total_amount = total_amount
    if invoice.total_amount > 0 :
        invoice.completed = True
    invoice.save()
    return invoice
    
def generate_pdf_invoice(request, invoice_id):
    """Generate PDF Invoice"""
    invoice = Invoice.objects.get(id=invoice_id)
    #
    cart = sh_models.ShopCart.objects.get(created_by=invoice.created_by)

    client = invoice.client
    created_by = invoice.created_by
    invoice_items = invoice.items.all()
    #raise Exception("invoice items = ", invoice.id)
    context = {
        "invoice": invoice,
        "client": client,
        "created_by": created_by,
        "invoice_items": invoice_items,
        #"host": request.get_host(),
        "host": "localhost",
    }
    #raise Exception("items = ", invoice_items[0].subtotal)
    
    
    html_template = render_to_string("pdf/html-invoice.html", context)

    pdf_file = HTML(
        string=html_template, base_url=request.build_absolute_uri()
    ).write_pdf()
    pdf_filename = f"invoice_{invoice.id}.pdf"
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "filename=%s" % (pdf_filename)
    return response


def simple_upload(request):
    if request.method == "POST" and request.FILES["myfile"]:
        myfile = request.FILES["myfile"]
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return render(
            request, "simple_upload.html", {"uploaded_file_url": uploaded_file_url}
        )
    return render(request, "simple_upload.html")
