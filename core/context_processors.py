from django.conf import settings as app_settings
from customer.models import Customer, VisitingCustomer
from shop.models import ShopCart 


def shop(request):
    try:
        cart = ShopCart.objects.get_or_create_from_request(request)
    except AttributeError:
        # Si get_or_create_from_request n'existe pas ou échoue
        cart = ShopCart.objects.filter(session_key=request.session.session_key).first()
        if not cart:
            cart = ShopCart.objects.create(session_key=request.session.session_key)
    
    return {'cart': cart}
    
def customer(request):
    """
    Add the customer to the RequestContext
    """
    msg = "The request object does not contain a customer. Edit your MIDDLEWARE_CLASSES setting to insert 'shop.middlerware.CustomerMiddleware'."
    assert hasattr(request, 'customer'), msg
    
    customer = request.customer
    #
    if request.user.is_staff:
        try:
            customer = Customer.objects.get(pk=request.session['emulate_user_id'])
        except Customer.DoesNotExist:
            customer = VisitingCustomer()
        except (AttributeError, KeyError):
            pass
    return {'customer': customer}


def shop_settings(request):
    """
    Add configuration settings to the context to customize the shop's settings in templates
    """
    from dj_rest_auth.serializers import LoginSerializer

    return {
        'header_bg_image' : app_settings.BG_IMG, 
        'site_header': app_settings.APP_LABEL.capitalize(),
        'ALLOW_SHORT_SESSIONS': 'stay_logged_in' in LoginSerializer().fields,
        'LINK_TO_EMPTY_CART': app_settings.LINK_TO_EMPTY_CART,
        'APP_LABEL': app_settings.APP_LABEL,
        'SHOP_APP_LABEL': app_settings.SHOP_APP_LABEL
    }
