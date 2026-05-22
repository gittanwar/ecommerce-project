from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.db.models import Q
from django.db import models  # ← IMPORTANT
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Product, Category
from accounts.models import Favourite

from .models import ContactMessage


# views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Newsletter


def contact_submit(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        messages.success(request, "Your message has been sent successfully! 🎉")

        return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect("/")

def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if Newsletter.objects.filter(email=email).exists():
            messages.warning(request, "You are already subscribed!")
        else:
            Newsletter.objects.create(email=email)
            messages.success(request, "Subscribed successfully!")

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect("/")


def get_products_ajax(request):
    """AJAX endpoint for filtering products by category"""
    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    products = Product.objects.filter(available=True)
    
    # Category filter
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Search filter
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Render products HTML
    html = render_to_string('store/products_partial.html', {'products': products})
    
    return JsonResponse({
        'success': True,
        'html': html,
        'count': products.count()
    })


def product_list(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    # Get latest product for hero section
    latest_product = Product.objects.filter(available=True).order_by('-created_at').first()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Pagination - Show 6 products per page
    paginator = Paginator(products, 6)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    return render(request, 'store/product_list.html', {
        'products': products_page,
        'categories': categories,
        'search_query': search_query,
        'latest_product': latest_product,
        'has_next': products_page.has_next(),
        'has_previous': products_page.has_previous(),
        'page_number': products_page.number,
        'total_pages': paginator.num_pages,
    })


def product_detail(request, slug):
    """Single product detail page with related products"""
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # Get related products (same category, exclude current product)
    related_products = Product.objects.filter(
        category=product.category, 
        available=True
    ).exclude(id=product.id)[:8]
    
    # Check if product is in user's favourites
    is_favourite = False
    if request.user.is_authenticated:
        is_favourite = Favourite.objects.filter(user=request.user, product=product).exists()
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'is_favourite': is_favourite
    })


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            send_mail(
                f'Contact Form: {subject}',
                f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}',
                email,
                [settings.DEFAULT_FROM_EMAIL] if hasattr(settings, 'DEFAULT_FROM_EMAIL') else ['admin@example.com'],
                fail_silently=True,
            )
            messages.success(request, 'Thank you! Your message has been sent.')
        except:
            messages.success(request, 'Message received! We will contact you soon.')
        
        return redirect('contact')
    
    return render(request, 'store/contact.html')


def shop_view(request):
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    # Add product count to each category
    for category in categories:
        category.product_count = Product.objects.filter(category=category, available=True).count()
    
    total_products = products.count()
    
    # Get max price for price filter
    max_price = products.aggregate(models.Max('price'))['price__max'] or 10000
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    # Pagination - 9 products per page
    paginator = Paginator(products, 9)
    page = request.GET.get('page', 1)
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    return render(request, 'store/shop.html', {
        'products': products_page,
        'categories': categories,
        'search_query': search_query,
        'total_products': total_products,
        'max_price': int(max_price),
    })


def about_view(request):
    return render(request, 'store/about.html')


def quick_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    data = {
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'price': str(product.price),
        'description': product.description,
        'image_url': product.image.url if product.image else '',
        'category': product.category.name,
        'stock': product.stock,
    }
    return JsonResponse(data)


@require_POST
def add_to_cart_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str]['quantity'] += 1
    else:
        cart[product_id_str] = {
            'quantity': 1,
            'price': str(product.price),
        }
    
    request.session['cart'] = cart
    
    # Get cart count
    cart_count = sum(item['quantity'] for item in cart.values())
    
    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'message': f'{product.name} added to cart!'
    })


@login_required
def check_favourite(request, product_id):
    """Check if product is in user's favourites (AJAX)"""
    is_favourite = Favourite.objects.filter(user=request.user, product_id=product_id).exists()
    return JsonResponse({'is_favourite': is_favourite})


@login_required
def toggle_favourite_detail(request, product_id):
    """Toggle favourite from product detail page - AJAX"""
    product = get_object_or_404(Product, id=product_id)
    favourite, created = Favourite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        favourite.delete()
        is_favourite = False
        message = 'Removed from favourites 💔'
    else:
        is_favourite = True
        message = 'Added to favourites ❤️'
    
    return JsonResponse({
        'success': True,
        'is_favourite': is_favourite,
        'message': message
    })