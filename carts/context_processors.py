from .models import CartItem, Cart
from .views import _cart_id

def product_count(request):
    count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:

            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart)
            for cart_item in cart_items:
                count = count + cart_item.quantity
        except Cart.DoesNotExist:
            count = 0
    return {"count": count}