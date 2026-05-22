from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from store.models import Product
from .models import Cart, CartItem

def get_or_create_cart(user):
    """Get or create cart for user"""
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

def merge_session_cart_with_db(request, user):
    """Merge session cart with database cart when user logs in"""
    session_cart = request.session.get('cart', {})
    
    if session_cart:
        cart = get_or_create_cart(user)
        
        for product_id_str, item_data in session_cart.items():
            try:
                product = get_object_or_404(Product, id=int(product_id_str))
                quantity = item_data.get('quantity', 1)
                
                # Check if item already exists in cart
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
            except:
                pass
        
        # Clear session cart after merge
        request.session['cart'] = {}
        request.session.modified = True

def cart_view(request):
    """View cart page"""
    if request.user.is_authenticated:
        cart = get_or_create_cart(request.user)
        cart_items = cart.items.all().select_related('product')
        total = cart.get_total()
    else:
        # For non-logged in users, use session cart
        session_cart = request.session.get('cart', {})
        cart_items = []
        total = 0
        
        for product_id_str, item in session_cart.items():
            try:
                product = get_object_or_404(Product, id=int(product_id_str))
                quantity = item['quantity']
                subtotal = product.price * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'id': product.id
                })
            except:
                pass
    
    return render(request, 'cart/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })

def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        # Logged in user - use database cart
        cart = get_or_create_cart(request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        messages.success(request, f'{product.name} added to cart!')
    else:
        # Non-logged in user - use session cart
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
        messages.success(request, f'{product.name} added to cart!')
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': get_cart_count(request),
            'message': f'{product.name} added to cart!'
        })
    
    return redirect('cart_view')

def update_cart(request, product_id):
    """Update cart item quantity"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if request.user.is_authenticated:
            cart = get_or_create_cart(request.user)
            cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
            
            if cart_item:
                if quantity > 0:
                    cart_item.quantity = quantity
                    cart_item.save()
                else:
                    cart_item.delete()
        else:
            cart = request.session.get('cart', {})
            product_id_str = str(product_id)
            
            if quantity > 0:
                if product_id_str in cart:
                    cart[product_id_str]['quantity'] = quantity
            else:
                if product_id_str in cart:
                    del cart[product_id_str]
            
            request.session['cart'] = cart
        
        return redirect('cart_view')

def remove_from_cart(request, product_id):
    """Remove item from cart"""
    if request.user.is_authenticated:
        cart = get_or_create_cart(request.user)
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
    else:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            del cart[product_id_str]
        
        request.session['cart'] = cart
    
    return redirect('cart_view')

def get_cart_count(request):
    """Get total items in cart"""
    if request.user.is_authenticated:
        cart = get_or_create_cart(request.user)
        return cart.get_item_count()
    else:
        cart = request.session.get('cart', {})
        return sum(item['quantity'] for item in cart.values())