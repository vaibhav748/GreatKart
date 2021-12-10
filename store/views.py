from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating
from category.models import Category
from carts.models import Cart, CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator
from .forms import ReviewRatingForm
from django.contrib import messages

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


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewRatingForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewRatingForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user = request.user
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)