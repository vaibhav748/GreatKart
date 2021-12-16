from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, UserProfileForm, UserForm
from .models import Account, UserProfile
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order, OrderProduct
import requests

#User Activation
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


# Create your views here.

def register(request):
    if request.method == 'POST':
        # import pdb;pdb.set_trace()
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # import pdb;pdb.set_trace()
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            username = email.split('@')[0]
            if password != confirm_password:
                messages.warning(request, 'Password does not match!')

            else:
                user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
                user.phone_number = phone_number
                user.save()

                # Create UserProfile
                profile = UserProfile()
                profile.user_id = user.id
                profile.profile_picture = 'default/default_image.png'
                profile.save()

                #USER ACTIVATION
                current_site = get_current_site(request)
                mail_subject = "Please activate your account"
                message = render_to_string("accounts/account_verification_email.html", {
                    'user': user,
                    'domain': current_site,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                })
                to_email = email
                send_email = EmailMessage(mail_subject, message, to=[to_email])
                send_email.send()
                # messages.success(request, 'Registration Successful.')
                # form = RegistrationForm()
                return redirect('/accounts/login/?command=verification&email='+email)

    else:
        form = RegistrationForm()

    data = {
        'form': form
     }
    return render(request, 'accounts/register.html', context=data)


def login_user(request):
    # import pdb;pdb.set_trace()
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    #Getting the product variations by cart_id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Getting the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variations = item.variations.all()
                        ex_var_list.append(list(existing_variations))
                        id.append(item.id)

                    if product_variation in ex_var_list:
                        # Increase the cartitem quantity.
                        index = ex_var_list.index(product_variation)
                        item_id = id[index]
                        item = CartItem.objects.get(id=item_id)
                        item.quantity += 1
                        item.user = user
                        item.save()
                    else:
                        cart_item = CartItem.objects.filter(cart=cart)
                        for item in cart_item:
                            item.user = user
                            item.save()
            except:
                pass

            login(request, user)
            messages.success(request, 'Logged In Successfully!!')
            # import pdb;pdb.set_trace()
            url = request.META.get("HTTP_REFERER")
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextpage = params['next']
                    return redirect(nextpage)
            except:
                return redirect('dashboard')
        else:
            messages.warning(request, "Invalid Credentials!!")
            return redirect('login')
    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout_user(request):
    logout(request)
    messages.success(request, 'Logged Out Successfully!!')
    return redirect('login')


def activate(request, uidb64, token):

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated.')
        return redirect('login')
    else:
        messages.error(request, 'Invalid activation link.')
        return redirect('register')


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.filter(user=request.user)
    orders_count = orders.count()
    # print(orders, orders_count)

    userprofile = UserProfile.objects.get(user_id=request.user.id)

    context = {
        'orders_count': orders_count,
        'userprofile': userprofile
    }
    return render(request, 'accounts/dashboard.html', context)


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        is_exists = Account.objects.filter(email=email).exists()
        if is_exists:
            user = Account.objects.get(email__iexact=email)

            # RESET PASSWORD EMAIL
            current_site = get_current_site(request)
            mail_subject = "Reset Your Password"
            message = render_to_string("accounts/reset_password_email.html", {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'We have sent you an email to your registered email ID.')
            return redirect('login')

        else:
            messages.warning(request, f'Account with the email {email} does not exists.')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(id=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please Reset Your Password.')
        return redirect('resetPassword')
    else:
        messages.warning(request, 'This link is expired')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(id=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password Reset Successful.')
            return redirect('login')

        else:
            messages.warning(request, 'Password Does Not Match!!')
            return redirect('resetPassword')

    return render(request, 'accounts/resetPassword.html')

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('created_at')
    print(orders)

    context = {
        'orders': orders
    }

    return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    # import pdb;pdb.set_trace()
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your Profile Has Been Updated.')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile': userprofile
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == "POST":
        current_password = request.POST["current_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            print(success)
            if success:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password Updated Successfully.")
                return redirect("change_password")
            else:
                messages.error(request, "Please Enter a Valid Current Password.")
                return redirect("change_password")
        else:
            messages.error(request, "Password Does Not Match.")
            return redirect("change_password")

    return render(request, 'accounts/change_password.html')


def order_detail(request, order_id, total=0):
    # import pdb;pdb.set_trace()
    order = Order.objects.get(order_number=order_id)
    order_details = OrderProduct.objects.filter(order=order)

    for item in order_details:
        total += (item.product.price * item.quantity)

    tax = total * 0.02
    grand_total = total + tax

    context = {
        'order': order,
        'order_details': order_details,
        'total': total,
        'tax': tax,
        'grand_total': grand_total
    }

    return render(request, 'accounts/order_detail.html', context)