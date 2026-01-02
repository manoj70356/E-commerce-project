from .models import Cart, CartItem
from .views import _cart_id

# def counter(request):
#   cart_count = 0
#   if 'admin' in request.path:
#       return {}
#   else:
#       try:
#           cart = Cart.objects.filter(cart_id=_cart_id(request))
#           if request.user.is_authenticated:
#             cart_items = CartItem.objects.all().filter(user=request.user)
#           else:
#             cart_items = CartItem.objects.all().filter(cart=cart[:1])
#           for cart_item in cart_items:
#               cart_count += cart_item.quantity
#       except Cart.DoesNotExist:
#           cart_count = 0
#   return dict(cart_count=cart_count)

from .models import Cart, CartItem
from .views import _cart_id

def counter(request):
    cart_count = 0

    if 'admin' in request.path:
        return {}

    try:
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)

        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        cart_count = sum(item.quantity for item in cart_items)

    except Cart.DoesNotExist:
        cart_count = 0

    return {'cart_count': cart_count}
