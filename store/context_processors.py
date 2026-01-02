from carts.views import _cart_id, Cart, CartItem

def counter(request):
    cart_count = 0

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart)

        for item in cart_items:
            cart_count += item.quantity

    except Cart.DoesNotExist:
        pass

    return dict(cart_count=cart_count)
