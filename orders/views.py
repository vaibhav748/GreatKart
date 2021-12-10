from django.shortcuts import render, redirect
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from store.models import Product
import datetime
import json
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.http import JsonResponse
# Create your views here.

def payments(request):
    # print(request.body)
    body = json.loads(request.body)
    # print(body)

    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body["orderID"])

    # Store the transaction details inside the Payment Model.
    payment = Payment(
        user=request.user,
        payment_id=body["transID"],
        payment_method=body["payment_method"],
        status=body["status"],
        amount_paid=order.order_total

    )
    payment.save()
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart_items to OrderProduct table.
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product.id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.is_ordered = True
        orderproduct.save()

        # Setting the variations
        cart_item = CartItem.objects.get(id=item.id)
        product_variations = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variations)
        orderproduct.save()



    # Reduce the quantity of the sold products.

        order_product = OrderProduct.objects.get(id=orderproduct.id)
        product = Product.objects.get(product_name=order_product.product.product_name)
        product.stock = product.stock - order_product.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order received email to customer
    mail_subject = "Thank you for your order."
    message = render_to_string("orders/order_received_email.html", {
        'user': request.user,
        'order': order

    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order_number and transaction ID back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id
    }
    return JsonResponse(data)
    # return render(request, 'orders/payments.html')

def place_order(request, total=0, quantity=0):
    user = request.user

    cart_items = CartItem.objects.filter(user=user)
    cart_items_count = cart_items.count()

    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = total * 0.02
    grand_total = total + tax

    if cart_items_count <= 0:
        return redirect('store')

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():

            # Store all the  billing information inside Order table.
            data = Order()
            data.user = user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order_number
            yr = int(datetime.date.today().strftime("%Y"))
            mn = int(datetime.date.today().strftime("%m"))
            d = int(datetime.date.today().strftime("%d"))
            d = datetime.date(yr, mn, d)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            # import pdb;pdb.set_trace()
            order = Order.objects.get(user=user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total
            }
            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')


def order_complete(request, total=0):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order.status = 'Accepted'
        order.save()
        ordered_products = OrderProduct.objects.filter(order=order)

        for item in ordered_products:
            total += (item.product.price * item.quantity)

        tax = total * 0.02
        grand_total = total + tax
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'total': total,
            'tax': tax,
            'grand_total': grand_total
        }
        return render(request, 'orders/order_complete.html', context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

