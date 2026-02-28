from django.conf import settings as app_settings
from customer.models import Customer, VisitingCustomer
from shop.models import ShopCart


def shop(request):
    """
    Context processor to add the cart to the request context.
    """
    # Try to get session key from request
    session_key = getattr(request.session, 'session_key', None)
    
    if session_key:
        # Try to get existing cart by session key
        cart = ShopCart.objects.filter(session_key=session_key, status='ACT').first()
        if not cart:
            # Create a new cart for anonymous users
            # Use a default user or None
            from django.contrib.auth import get_user_model
            User = get_user_model()
            default_user, _ = User.objects.get_or_create(
                username='anonymous',
                defaults={'is_active': False}
            )
            cart = ShopCart.objects.create(
                created_by=default_user,
                session_key=session_key,
                status='ACT'
            )
    else:
        cart = None
    
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
