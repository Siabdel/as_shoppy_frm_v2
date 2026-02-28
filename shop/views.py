
# product/views.py
from typing import Any
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView
from django.contrib import messages
from django.utils import timezone
from core.utils import get_product_model, Dict2Obj
from product import models as pro_models
from shop import models as msh_models 
from product import models as pro_models
from django.conf import settings
from .forms import CartAddProductForm
from .models import ShopCart, CartItem
from customer import models as cli_models
from customer import views as cli_views

# product Model setting
product_model = get_product_model()

class ClientCheck(ListView):
    template_name = "shop/client_checkout.html"

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return cli_models.Customer.objects.filter(created_by=self.request.user)
        else:
            return cli_models.Customer.objects.none()


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

    
def cart_add_one_item(request, product_id):
    cart = ShopCart.objects.get_or_create_cart(request.user)  # create a new cart object passing it the request object 
    product = get_object_or_404(product_model, id=product_id) 
    champs = [f.name for f in CartItem._meta.get_fields()]
    ## raise Exception(" des champs ", champs)
    cart.add_product(product=product,)
    return redirect('cart:cart_detail')
    

@require_POST
def cart_add_item(request, product_id):
    cart = ShopCart.objects.get_or_create_from_request(request)  # create a new cart object passing it the request object 
    product = get_object_or_404(pro_models.Product, id=product_id) 
    form = CartAddProductForm(request.POST)
    
    if form.is_valid():
        cdata = form.cleaned_data
        cart.add(product=product, quantity=cdata['quantity'], update_quantity=True)
    return redirect('cart:cart_detail')

def cart_remove_item(request, product_id):
    cart = ShopCart.objects.get_or_create_from_request(request)
    product = get_object_or_404(pro_models.Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = ShopCart.objects.get_or_create_from_request(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'update': True})
    return render(request, 'cart/detail.html', {'cart': cart})

def print_pdf(request):
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


def cart_summary(request):
    cart_items = CartItem.objects.filter(cart__created_by=request.user)
    total = sum(item.total_price for item in cart_items)
    #return redirect('cart:cart_detail')
    return render(request, 'shop/cart_summary.html', {'cart_items': cart_items, 'total': total})


# Delivery methods with pricing
DELIVERY_METHODS = [
    {'id': 'standard', 'name': 'Standard Delivery', 'price': 9.99, 'days': '5-7 business days'},
    {'id': 'express', 'name': 'Express Delivery', 'price': 19.99, 'days': '2-3 business days'},
    {'id': 'pickup', 'name': 'Store Pickup', 'price': 0, 'days': 'Same day (if ordered before 2pm)'},
]


def checkout(request):
    """Checkout view for CMagic Sport"""
    from core.cart.cart import Cart
    
    cart = Cart(request)
    
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:cart_detail')
    
    # Calculate totals
    subtotal = cart.get_total_price()
    shipping = 9.99 if subtotal < 100 else 0
    tax = subtotal * 0.10  # 10% tax
    total = subtotal + shipping + tax
    
    if request.method == 'POST':
        # Process the checkout form
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        delivery_method = request.POST.get('delivery_method', 'standard')
        payment_method = request.POST.get('payment_method', 'credit_card')
        notes = request.POST.get('notes', '')
        
        # Get delivery cost
        delivery_cost = 0
        for method in DELIVERY_METHODS:
            if method['id'] == delivery_method:
                delivery_cost = method['price']
                break
        
        # Calculate final total with selected delivery
        final_total = subtotal + (delivery_cost if delivery_cost > 0 else 0) + tax
        
        # Create order (placeholder - would need Order model)
        order_id = f"ORD-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Clear the cart
        cart.clear()
        
        # Redirect to success page
        return render(request, 'shop/checkout_success.html', {
            'order_id': order_id,
            'first_name': first_name,
            'email': email,
            'total': final_total,
            'delivery_method': delivery_method,
            'payment_method': payment_method,
        })
    
    # GET request - show checkout form
    return render(request, 'shop/checkout_cmagic.html', {
        'cart': cart,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'delivery_methods': DELIVERY_METHODS,
    })


def checkout_success(request):
    """Order confirmation page"""
    order_id = request.GET.get('order_id', 'N/A')
    return render(request, 'shop/checkout_success.html', {'order_id': order_id})
