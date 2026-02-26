from shop.models import ShopCart


def cart(request):
    return {'cart': ShopCart(request)}

