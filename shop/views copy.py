
# product/views.py
from typing import Any
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from core.utils import get_product_model, Dict2Obj
from product import models as pro_models
from shop import models as msh_models 
from product import models as pro_models
from django.conf import settings
from .forms import CartAddProductForm

# product Model setting
product_model = get_product_model()

def category_list(request, categoy_slug=None ):
    category = get_object_or_404(pro_models.MPCategory, slug=categoy_slug)
    products = pro_models.Product.objects.filter(
        category__in = pro_models.MPCategory.objects
        .get(name=categoy_slug).get_descendants(include_self=False)
    )
    context = {
            "categoy": category,
            "products": products,
            }
    return render(request, "product/category_list.html", context=context)
    

def product_shop_ist(request, category_slug=None):
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
    return render(request, "product/product_detail.html", context=pro_context)

def product_shop_home(request, category_slug=None):
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
    return render(request, "product/home.html", context=context)

@login_required
def product_shop_list(request, category_slug=None):
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
    return render(request, "product/product_list.html", context=context)

def product_shop_detail(request, product_id, slug):
    return render(request, "product/product_detail.html", context={})

class ProductDetailView(DetailView): # new
    model = pro_models.Product
    template_name = "product/product_detail.html"
    context_object_name = "product"
    
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        
        context =  super().get_context_data(**kwargs)
        # formulaire 
        cart_product_form = CartAddProductForm()
        # Récupérer les images associées à ce produit en utilisant la méthode que nous avons définie dans le modèle
        product = self.get_object()
        product_images = product.get_images()
        # les psecifications du produit 
        ## raise Exception("options = ", product.options)

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
            'cart_product_form': cart_product_form,
            'app_name' : 'carshop',
        }
      
        return context

def order_create(request):
    cart = Cart(request) 
    cart_id = request.session[settings.CART_SESSION_ID]
    #raise Exception(f" cart={cart}, card_id={cart_id}")
    
    shop_cart = msh_models.ShopCart.objects.get(id=cart_id)
    items = shop_cart.item_articles.all()
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            # vider le panier 
            cart.clear()
        return render(request, 'orders/order/created.html', {'order': order})
    else:
        form = OrderCreateForm()
        context = {
                    'items':items,
                    'form': form
                   }
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