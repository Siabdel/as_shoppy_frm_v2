
# Dajango Contrib
from typing import Any
from django.forms.models import BaseModelForm
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.utils.decorators import method_decorator
from django.db import transaction   
from immoshop.forms import CustomFormSet
from customer.forms import CustomCreatForm, AccountUserCreationForm
from django.views import View




## Generic View
from django.views.generic import (
    View,
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.views import View
## local app modules
from weasyprint import HTML
from core.orders.models import OrderItem
from product import models as pro_models
from shop import models as sh_models 
from customer import models as cu_models 
from immoshop import models as immo_models
from invoices import models as devis_models
from shop.models import ShopCart
from django.urls import reverse, resolve
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from customer.forms import CustomCreatForm, AccountUserCreationForm
from core.utils import get_product_model, Dict2Obj
from core.cart__.forms import CartAddProductForm
from core.taxonomy import models as tax_models
from django.shortcuts import get_object_or_404



# product Model setting
product_model = get_product_model()

def category_list(request, categoy_slug=None ):
    category = get_object_or_404(pro_models.MPCategory, slug=categoy_slug)
    products = pro_models.ImmoProduct.objects.filter(
        category__in = pro_models.MPCategory.objects
        .get(name=categoy_slug).get_descendants(include_self=False)
    )
    context = {
            "categoy": category,
            "products": products,
            }
    return render(request, "immoshop/category_list.html", context=context)
    

def product_list(request, category_slug=None):
    category = None
    categories = pro_models.MPCategory.objects.all()
    products = pro_models.Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(pro_models.MPCategory, slug=category_slug)
        products = pro_models.Product.objects.filter(category=category)

    pro_context = {
        'category': category,
        'categories': categories,
        'products': products
    }
    return render(request, "immoshop/product_detail.html", context=pro_context)

def product_home(request, category_slug=None):
    products_list = product_model.objects.all()
    category = None
    categories = pro_models.MPCategory.objects.all()
    #
    if category_slug:
        category = get_object_or_404(pro_models.MPCategory, slug=category_slug)
    
    # ProductSpecificationValues
    for product in products_list:
        options = [] 
        psv = pro_models.ProductSpecificationValue.objects.filter(product=product)
        for spec in psv:
            attributes = {"product": spec.product.id,
                       "name": spec.specification.name,
                       "value": spec.value,
                    }
            options.append(Dict2Obj(attributes))
        ## add options
        product.options = options
    
    context = { 'products' : products_list,
                'category': category,
                'categories': categories,
                'cart_product_form' : CartAddProductForm()
               } 
    return render(request, "immoshop/home.html", context=context)

@login_required
def product_immo_list(request, category_slug=None):
    products_list = product_model.objects.all()
    category = None
    categories = pro_models.MPCategory.objects.all()
    #
    if category_slug:
        category = get_object_or_404(pro_models.MPCategory, slug=category_slug)
    
    context = { 'products' : products_list,
                'category': category,
                'categories': categories,
                'cart_product_form' : CartAddProductForm()
               } 
    return render(request, "immoshop/product_list.html", context=context)

def product_immo_detail(request, product_id, slug):
    return render(request, "immoshop/product_detail.html", context={})

class ProductDetailView(DetailView): # new
    model = immo_models.ImmoProduct
    template_name = "immoshop/product_detail.html"
    context_object_name = "product"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        
        context =  super().get_context_data(**kwargs)
        # formulaire 
        cart_product_form = CartAddProductForm()
        # Récupérer les images associées à ce produit en utilisant la méthode que nous avons définie dans le modèle
        product = self.get_object()
        product_images = product.images.all()
        # les psecifications du produit 
        
        options = [] 
        psv = pro_models.ProductSpecificationValue.objects.filter(product=product)
        for spec in psv:
            attributes = {"product": spec.product.id,
                       "name": spec.specification.name,
                       "value": spec.value,
                    }
            options.append(Dict2Obj(attributes))
        ## add options
        product.options = options

        context = {
            'product':  product,
            'product_images' : product_images,
            'image' : product_images.first(),
            'cart_product_form': cart_product_form
        }
      
        return context
    
class InvoiceCreate(View):
    template_name = "immoshop/create.html"
    form_class = CustomCreatForm

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context =  super().get_context_data(**kwargs)
        # formulaire 
        custom_form = self.form_class()
        context = context.upoadet({
            'form': custom_form
        })
      
        return context
        
    def get(self, request, user_id):
        #
        user = User.objects.get(pk=user_id)
        form = self.form_class(initial={"user": user})
        ## 
        return render(request, self.template_name, {"form": form})
    
    def post(self, request, *args, **kwargs):
        # cart 
        cart = ShopCart(request) 
        cart_id = request.session[settings.CART_SESSION_ID]

        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            shop_cart = sh_models.ShopCart.objects.get(id=cart_id)
            items = shop_cart.item_articles.all()
            # 1- create client 
            form.instance.user = request.user
            customer  = form.save()
            
            # 2- create invoice + ItemInvoice
            devis = devis_models.Invoice(title="Mon devis test", 
                                         client = customer, 
                                         invoice_total = 100,
                                         )
            for item in items:
                devis_models.InvoiceItem.objects.create(
                    invoice = devis,
                    item = item, 
                    quantity=item.quantity,
                    rate = 12,
                    tax = 15.5, 
                    price=item.product.price,
                )
            # vider le panier 
            cart.clear()
            
            ## url = reverse('invoice-detail', kwargs={'pk' : devis.pk}) 
            #response =  redirect('invoice:invoice-detail')
            return redirect('invoice_detail', pk=devis.pk)
        else :
            user = form.instance.user
            #return redirect('invoice_create', user_id=user.pk)
            return render(request, self.template_name, {"form": form})
    
    
    
def invoice_create(request):
    """ 
    1- create client user
    2- create invoice + ItemInvoice
    3- Valider la commande ou la reservation
    """
    cart = ShopCart(request) 
    cart_id = request.session[settings.CART_SESSION_ID]
    #raise Exception(f" cart={cart}, card_id={cart_id}")
    context = {} 
    shop_cart = sh_models.ShopCart.objects.get(id=cart_id)
    items = shop_cart.item_articles.all()
    
    if request.method == 'POST':
        form = CustomCreatForm(request.POST)
        if form.is_valid():
            # 1- create client 
            customer  = form.save()
            # 2- create invoice + ItemInvoice
            devis = devis_models.Invoice(title="Mon devis test", 
                                         client = customer, 
                                         invoice_total = 100,
                                         )
            for item in items:
                devis_models.InvoiceItem.objects.create(
                    invoice = devis,
                    item = item, 
                    quantity=item.quantity,
                    rate = 12,
                    tax = 15.5, 
                    price=item.product.price,
                )
            # vider le panier 
            cart.clear()
            ## url = reverse('invoice-detail', kwargs={'pk' : devis.pk}) 
            #response =  redirect('invoice:invoice-detail')
            return redirect('invoice_detail', pk=devis.pk)
    else:
        form = CustomCreatForm()
        context = { 'items':items, 'form': form }

    return render(request, 'orders/order/create.html', context )

        
@login_required
def generate_pdf_invoice(request, invoice_id):
    """Generate PDF Invoice"""

    queryset = Invoice.objects.filter(user=request.user)
    invoice = get_object_or_404(queryset, pk=invoice_id)

    client = invoice.client
    user = invoice.user
    invoice_items = InvoiceItem.objects.filter(invoice=invoice)

    context = {
        "invoice": invoice,
        "client": client,
        "user": user,
        "invoice_items": invoice_items,
        "host": request.get_host(),
    }
    print(request.get_host())

    html_template = render_to_string("pdf/html-invoice.html", context)

    pdf_file = HTML(
        string=html_template, base_url=request.build_absolute_uri()
    ).write_pdf()
    
    pdf_filename = f"invoice_{invoice.id}.pdf"
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "filename=%s" % (pdf_filename)
    return response


 
class CreateAccount(View):
    template_name = "immoshop/create_account_vuejs.html"
    form_class = AccountUserCreationForm
    currentPage = 1
    form1_validate = 0
    form2_validate = 0

    def get(self, request):
        account_form = AccountUserCreationForm()
        custom_formset = CustomFormSet()
        context = {
            'account_form': account_form, 
            'custom_formset': custom_formset,
            'currentPage' : self.currentPage ,
            'form1_validate' : self.form1_validate,
            'form2_validate' : self.form2_validate,
        }
        messages.add_message(self.request, messages.INFO,
                             f"CreateAccount get() = { request.GET }")
        return render(request, self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        account_form = AccountUserCreationForm(request.POST, prefix='account')
        custom_formset = CustomFormSet(request.POST, prefix='custom')

        messages.add_message(self.request, messages.INFO,
                             f"CreateAccount post() = { request.POST }")

        if account_form.is_valid() and custom_formset.is_valid():
            account_instance = account_form.save()
            custom_formset.instance = account_instance
            custom_formset.save()

        if account_form.is_valid(): 
            self.form1_validate = 1
            
        elif custom_formset.is_valid():
            self.form2_validate = 1
  
        context = {
            'account_form': account_form, 
            'custom_formset': custom_formset,
            'currentPage' : self.currentPage,
            'form1_validate' : self.form1_validate,
            'form2_validate' : self.form2_validate,
        }

        messages.add_message(self.request, messages.INFO, 
                             f"CreateAccount POST : vform1={self.form1_validate} vform2 = {self.form2_validate}")
        return render(request, self.template_name, context=context)


def success(request):
    return render(request, 'immoshop/success.html')

def create_client(request, user_id):
    author = User.objects.get(id=user_id)
    books = Book.objects.filter(author=author)
    formset = CustomFormSet(request.POST or None)
 
    if request.method == "POST":
        if formset.is_valid():
            formset.instance = author
            formset.save()
            return redirect("create-book", pk=author.id)
 
    context = {
        "formset": formset,
        "author": author,
        "books": books
    }
 
    return render(request, "create_book.html", context)
    
