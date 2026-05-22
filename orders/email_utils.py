from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    subject = f'Order Confirmation #{order.id} - MyStore'
    
    # HTML email template
    html_message = render_to_string('orders/email/order_confirmation.html', {
        'order': order,
        'customer_name': order.full_name,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        html_message=html_message,
        fail_silently=False,
    )

def send_admin_order_notification(order):
    """Send new order notification to admin"""
    subject = f'New Order #{order.id} - MyStore'
    
    html_message = render_to_string('orders/email/admin_notification.html', {
        'order': order,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        html_message=html_message,
        fail_silently=False,
    )

def send_order_status_update_email(order, old_status, new_status):
    """Send order status update email to customer"""
    subject = f'Order #{order.id} Status Updated - MyStore'
    
    html_message = render_to_string('orders/email/status_update.html', {
        'order': order,
        'old_status': old_status,
        'new_status': new_status,
    })
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        html_message=html_message,
        fail_silently=False,
    )