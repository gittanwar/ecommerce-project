from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from store.models import Product
from .models import Favourite
# from cart.views import merge_session_cart_with_db
import random

from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages

# SEND OTP
def send_otp(request):

    if request.method == "POST":

        email = request.POST.get("email")

        otp = random.randint(100000, 999999)

        # save in session
        request.session['email_otp'] = str(otp)

        request.session['otp_email'] = email

        send_mail(
            'Your Login OTP',
            f'Your OTP is: {otp}',
            'dktanwar129@gmail.com',
            [email],
            fail_silently=False,
        )

        messages.success(request, "OTP sent successfully")

        return redirect('verify_otp')

    return render(request, 'accounts/send_otp.html')

def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get(
            "otp",
            ""
        ).strip()

        saved_otp = str(
            request.session.get(
                'email_otp',
                ''
            )
        ).strip()

        email = request.session.get(
            'otp_email'
        )

        # DEBUG
        print("ENTERED OTP:", entered_otp)

        print("SAVED OTP:", saved_otp)

        print("EMAIL:", email)

        # SESSION EXPIRED
        if not email:

            messages.error(
                request,
                "Session expired. Please resend OTP."
            )

            return redirect('login')

        # OTP MATCH
        if entered_otp == saved_otp:

            # CHECK USER EXISTS
            user = User.objects.filter(
                email=email
            ).first()

            # CREATE USER
            if not user:

                username = email.split("@")[0]

                base_username = username

                counter = 1

                while User.objects.filter(
                    username=username
                ).exists():

                    username = (
                        f"{base_username}{counter}"
                    )

                    counter += 1

                user = User.objects.create_user(

                    username=username,

                    email=email,

                    password=None

                )

            # LOGIN USER
            login(
    request,
    user,
    backend='django.contrib.auth.backends.ModelBackend'
)

            # CLEAR SESSION
            request.session.pop(
                'email_otp',
                None
            )

            request.session.pop(
                'otp_email',
                None
            )

            messages.success(
                request,
                "Login Successful"
            )

            return redirect(
                'product_list'
            )

        else:

            messages.error(
                request,
                "Invalid OTP"
            )

    return render(
        request,
        'accounts/verify_otp.html'
    )


def resend_otp(request):

    email = request.session.get('otp_email')

    if not email:

        messages.error(
            request,
            "Session expired"
        )

        return redirect('login')

    otp = random.randint(100000, 999999)

    # SAVE NEW OTP
    request.session['email_otp'] = str(otp)

    send_mail(
        'Your New OTP',
        f'Your new OTP is: {otp}',
        'yourgmail@gmail.com',
        [email],
        fail_silently=False,
    )

    messages.success(
        request,
        "New OTP sent successfully"
    )

    return redirect('verify_otp')

@login_required
def toggle_favourite(request, product_id):
    """Add or remove product from favourites"""
    product = get_object_or_404(Product, id=product_id)
    favourite, created = Favourite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        favourite.delete()
        is_favourite = False
        message = f'{product.name} removed from favourites'
    else:
        is_favourite = True
        message = f'{product.name} added to favourites'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favourite': is_favourite,
            'message': message,
            'favourite_count': Favourite.objects.filter(user=request.user).count()
        })
    
    return redirect('favourite_list')

@login_required
def favourite_list(request):
    """Show user's favourite products"""
    favourites = Favourite.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'accounts/favourites.html', {'favourites': favourites})

# Signup View
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('signup')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'accounts/signup.html')

# Login View
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('product_list')
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'accounts/login.html')

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('product_list')

# Profile View (Optional)
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')