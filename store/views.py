from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import Product
from category.models import Category
from carts.models import Cart, CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
# Create your views here.

def store(request, category_slug=None):

    if category_slug is not None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(Q(category=categories) & Q(is_available=True))
        paginator = Paginator(products, 2)
        page_number = request.GET.get('page')
        paged_products = paginator.get_page(page_number)
        product_count = products.count()

    else:
        products = Product.objects.filter(is_available=True).order_by("id")
        paginator = Paginator(products, 3)
        page_number = request.GET.get('page')
        paged_products = paginator.get_page(page_number)
        product_count = products.count()

    data = {
        'products': paged_products,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context=data)


def product_detail(request, category_slug, product_slug):
    try:
        # import pdb;pdb.set_trace()
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()
        cart_item = CartItem.objects.filter(cart=cart, product=single_product).exists()
    except Exception as e:
        raise e
    data={
        'single_product': single_product,
        'cart_item': cart_item
    }
    return render(request, 'store/product_detail.html', context=data)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        data = {'product_count': 0}
        if keyword:
            products = Product.objects.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword)).order_by('-created_date')
            product_count = products.count()
            data = {
                'products': products,
                'product_count': product_count
            }
    return render(request, 'store/store.html', context=data)