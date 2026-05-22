from django.db import models
from django.contrib.auth.models import User
from store.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Coupon/discount support
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, default='COD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ========== TRACKING FIELDS (Add these inside Order class) ==========
    tracking_number = models.CharField(max_length=50, null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    def get_status_timeline(self):
        """Get order status timeline"""
        timeline = [
            {'status': 'pending', 'label': 'Order Placed', 'icon': 'fa-shopping-cart', 'date': self.created_at},
        ]
        
        if self.status == 'processing':
            timeline.append({'status': 'processing', 'label': 'Processing', 'icon': 'fa-cog', 'date': self.updated_at})
        elif self.status == 'shipped':
            timeline.append({'status': 'processing', 'label': 'Processing', 'icon': 'fa-cog', 'date': self.updated_at})
            timeline.append({'status': 'shipped', 'label': 'Shipped', 'icon': 'fa-truck', 'date': self.updated_at})
        elif self.status == 'delivered':
            timeline.append({'status': 'processing', 'label': 'Processing', 'icon': 'fa-cog', 'date': self.updated_at})
            timeline.append({'status': 'shipped', 'label': 'Shipped', 'icon': 'fa-truck', 'date': self.updated_at})
            timeline.append({'status': 'delivered', 'label': 'Delivered', 'icon': 'fa-check-circle', 'date': self.delivered_at or self.updated_at})
        elif self.status == 'cancelled':
            timeline.append({'status': 'cancelled', 'label': 'Cancelled', 'icon': 'fa-times-circle', 'date': self.updated_at})
        
        return timeline
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def subtotal(self):
        return self.price * self.quantity


# Coupon discount
class Coupon(models.Model):
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (₹)'),
    )
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.IntegerField(default=1)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_to and 
                self.used_count < self.usage_limit)
    
    def calculate_discount(self, total_amount):
        if not self.is_valid():
            return 0
        
        if total_amount < self.minimum_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = (self.discount_value / 100) * total_amount
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = min(self.discount_value, total_amount)
        
        return discount
    
    class Meta:
        ordering = ['-created_at']


class UsedCoupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'coupon')