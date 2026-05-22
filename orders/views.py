from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.views.decorators.http import require_POST
from django.utils import timezone
from xhtml2pdf import pisa
from io import BytesIO
from django.contrib.admin.views.decorators import staff_member_required

from .models import Order, OrderItem, Coupon, UsedCoupon
from store.models import Product
from cart.models import Cart, CartItem
from decimal import Decimal

from django.conf import settings
from .email_utils import send_order_confirmation_email, send_admin_order_notification


@staff_member_required
def download_invoice(request, order_id):
    """Download order invoice as PDF"""
    order = get_object_or_404(Order, id=order_id)
    
    # Create HTML template for invoice
    template_path = 'orders/invoice.html'
    context = {'order': order}
    
    # Get HTML template
    template = get_template(template_path)
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
        return response
    
    return HttpResponse('Error generating PDF', status=400)


@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        
        # Restore stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
        
        messages.success(request, f'Order #{order.id} has been cancelled successfully!')
    else:
        messages.error(request, 'This order cannot be cancelled as it is already processed.')
    
    return redirect('my_orders')

@login_required
def checkout_view(request):
    """Checkout page - Database cart version"""
    
    # Get cart from database
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all().select_related('product')
    
    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('cart_view')
    
    # Calculate totals
    total = Decimal('0')
    items_list = []
    
    for item in cart_items:
        subtotal = item.product.price * item.quantity
        total += subtotal
        items_list.append({
            'product': item.product,
            'quantity': item.quantity,
            'subtotal': subtotal
        })
    
    # Get coupon from session
    coupon_data = request.session.get('coupon', {})
    coupon_code = coupon_data.get('code', '')
    discount = Decimal(str(coupon_data.get('discount', 0)))
    
    # Verify coupon is still valid
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            # Recalculate discount to ensure it's correct
            discount = coupon.calculate_discount(total)
            coupon_data['discount'] = float(discount)
            request.session['coupon'] = coupon_data
        except Coupon.DoesNotExist:
            # Coupon no longer exists, remove from session
            if 'coupon' in request.session:
                del request.session['coupon']
            discount = Decimal('0')
            coupon_code = ''
    
    final_total = total - discount
    
    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        payment_method = request.POST.get('payment_method')
        
        # Get updated coupon from session (in case it was applied)
        final_coupon_data = request.session.get('coupon', {})
        final_discount = Decimal(str(final_coupon_data.get('discount', 0)))
        final_total_amount = total - final_discount
        
        # Store order details in session for payment
        request.session['order_data'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'city': city,
            'state': state,
            'pincode': pincode,
            'payment_method': payment_method,
            'total': float(total),
            'discount': float(final_discount),
            'final_total': float(final_total_amount),
            'coupon_code': final_coupon_data.get('code', ''),
            'coupon_id': final_coupon_data.get('coupon_id', '')
        }
        
        # For Mock Payment, redirect to mock payment page
        if payment_method == 'mock_payment':
            return redirect('mock_payment')
        
        # For COD, create order directly
        elif payment_method == 'COD':
            order = create_order_from_db_cart(request)
            if order:
                messages.success(request, f'Order placed successfully! Order ID: #{order.id}')
                return redirect('order_confirmation', order_id=order.id)
            else:
                messages.error(request, 'Error creating order. Please try again.')
                return redirect('checkout')
    
    return render(request, 'orders/checkout.html', {
        'cart_items': items_list,
        'total': float(total),
        'discount': float(discount),
        'final_total': float(final_total),
        'user': request.user,
        'coupon_code': coupon_code
    })

@login_required
def mock_payment_view(request):
    """Mock Payment Page - Testing purpose only"""
    order_data = request.session.get('order_data', {})
    
    if not order_data:
        messages.error(request, 'No order found!')
        return redirect('checkout')
    
    if request.method == 'POST':
        payment_status = request.POST.get('payment_status', 'success')
        
        if payment_status == 'success':
            # Create order from database cart
            order = create_order_from_db_cart(request)
            messages.success(request, f'Payment Successful! Order placed successfully! Order ID: #{order.id}')
            return redirect('order_confirmation', order_id=order.id)
        else:
            messages.error(request, 'Payment Failed! Please try again.')
            return redirect('checkout')
    
    return render(request, 'orders/mock_payment.html', {
        'total': order_data.get('total', 0),
        'order_data': order_data
    })


def create_order_from_db_cart(request):
    """Create order from database cart"""
    order_data = request.session.get('order_data')
    
    if not order_data:
        return None
    
    # Get cart from database
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all().select_related('product')
    
    if not cart_items:
        return None
    
    # Calculate total
    total = Decimal('0')
    for item in cart_items:
        total += item.product.price * item.quantity
    
    # Get discount from order_data
    discount = Decimal(str(order_data.get('discount', 0)))
    final_total = total - discount
    
    # Create order
    order = Order.objects.create(
        user=request.user,
        full_name=order_data['full_name'],
        email=order_data['email'],
        phone=order_data['phone'],
        address=order_data['address'],
        city=order_data['city'],
        state=order_data['state'],
        pincode=order_data['pincode'],
        total_amount=final_total,
        original_amount=total,
        discount_amount=discount,
        payment_method=order_data['payment_method']
    )
    
    # Apply coupon if used
    coupon_id = order_data.get('coupon_id')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id, is_active=True)
            order.coupon = coupon
            order.save()
            
            coupon.used_count += 1
            coupon.save()
            
            UsedCoupon.objects.create(
                user=request.user,
                coupon=coupon,
                order=order
            )
            
            if 'coupon' in request.session:
                del request.session['coupon']
        except:
            pass
    
    # Create order items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
        
        # Reduce stock
        product = item.product
        product.stock -= item.quantity
        product.save()
    
    # Clear database cart
    cart.items.all().delete()
    
    # Clear session data
    if 'order_data' in request.session:
        del request.session['order_data']
    
    # ========== SEND EMAILS ==========
    try:
        # Send confirmation email to customer
        send_order_confirmation_email(order)
        print(f"Order confirmation email sent to {order.email}")
        
        # Send notification email to admin
        send_admin_order_notification(order)
        print(f"Admin notification email sent")
    except Exception as e:
        print(f"Email sending error: {e}")
    
    return order


@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


# ==================== COUPON FUNCTIONS ====================

@login_required
def apply_coupon(request):
    """Apply coupon to cart"""
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip().upper()
        
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            
            # Check if coupon is valid
            now = timezone.now()
            if not (coupon.valid_from <= now <= coupon.valid_to):
                messages.error(request, 'Coupon has expired!')
                return redirect('checkout')
            
            if coupon.used_count >= coupon.usage_limit:
                messages.error(request, 'Coupon usage limit reached!')
                return redirect('checkout')
            
            # Get cart total from database
            cart, created = Cart.objects.get_or_create(user=request.user)
            total = cart.get_total()
            
            # Check minimum order amount
            if total < coupon.minimum_order_amount:
                messages.error(request, f'Minimum order amount of ₹{coupon.minimum_order_amount} required for this coupon!')
                return redirect('checkout')
            
            # Calculate discount
            discount = coupon.calculate_discount(total)
            
            # Store coupon in session
            request.session['coupon'] = {
                'code': coupon_code,
                'discount': float(discount),
                'coupon_id': coupon.id
            }
            
            messages.success(request, f'Coupon "{coupon_code}" applied! You saved ₹{discount}')
            
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code!')
        
        return redirect('checkout')


@login_required
def remove_coupon(request):
    """Remove applied coupon"""
    if 'coupon' in request.session:
        del request.session['coupon']
        messages.success(request, 'Coupon removed!')
    return redirect('checkout')


@login_required
def track_order(request, order_id):
    """Customer order tracking page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    timeline = order.get_status_timeline()
    
    return render(request, 'orders/track_order.html', {
        'order': order,
        'timeline': timeline
    })

def track_order_by_number(request):
    """Track order by order number (without login)"""
    order = None
    message = None
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        email = request.POST.get('email')
        
        try:
            order = Order.objects.get(id=order_id, email=email)
        except Order.DoesNotExist:
            message = 'No order found with this Order ID and Email combination.'
    
    return render(request, 'orders/track_by_number.html', {
        'order': order,
        'message': message
    })