from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Order, OrderItem, Coupon, UsedCoupon

from .email_utils import send_order_status_update_email


class OrderItemInline(admin.TabularInline):
    """Order items inline in admin"""
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'subtotal_display']
    can_delete = False
    
    def subtotal_display(self, obj):
        return f"₹{obj.subtotal()}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_link', 'customer_info', 'total_amount_display', 'payment_method', 'status_badge', 'tracking_info', 'created_at', 'action_buttons']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['id', 'full_name', 'email', 'phone', 'user__username', 'tracking_number']
    readonly_fields = ['created_at', 'updated_at', 'original_amount', 'discount_amount']
    inlines = [OrderItemInline]
    list_per_page = 20
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'full_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'pincode')
        }),
        ('Order Details', {
            'fields': ('total_amount', 'original_amount', 'discount_amount', 'coupon', 'payment_method', 'status')
        }),
        ('Tracking Information', {
            'fields': ('tracking_number', 'estimated_delivery', 'delivered_at', 'notes'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    

    def save_model(self, request, obj, form, change):
        if change:
            # Get the original order from database
            original = Order.objects.get(pk=obj.pk)
            old_status = original.status
            new_status = obj.status
            
            if old_status != new_status:
                # Send status update email to customer
                try:
                    send_order_status_update_email(obj, old_status, new_status)
                except:
                    pass
        
        super().save_model(request, obj, form, change)



    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.id])
        return format_html('<a href="{}" target="_blank">#{}</a>', url, obj.id)
    order_link.short_description = 'Order #'
    
    def customer_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color:#666;">{}</small><br><small style="color:#666;">📞 {}</small>',
            obj.full_name, obj.email, obj.phone
        )
    customer_info.short_description = 'Customer'
    
    def total_amount_display(self, obj):
        if obj.discount_amount > 0:
            return format_html(
                '<span style="text-decoration:line-through; color:#999;">₹{}</span><br><strong style="color:#28a745;">₹{}</strong>',
                obj.original_amount, obj.total_amount
            )
        return format_html('<strong>₹{}</strong>', obj.total_amount)
    total_amount_display.short_description = 'Amount'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#856404',
            'processing': '#0c5460',
            'shipped': '#004085',
            'delivered': '#155724',
            'cancelled': '#721c24',
        }
        bg_colors = {
            'pending': '#fff3cd',
            'processing': '#d1ecf1',
            'shipped': '#cce5ff',
            'delivered': '#d4edda',
            'cancelled': '#f8d7da',
        }
        return format_html(
            '<span style="background: {}; color: {}; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;">{}</span>',
            bg_colors.get(obj.status, '#f0f0f0'),
            colors.get(obj.status, '#333'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def tracking_info(self, obj):
        if obj.tracking_number:
            return format_html(
                '<span style="font-size: 11px;">📦 {}</span><br>{}',
                obj.tracking_number,
                f'<small>Est: {obj.estimated_delivery}</small>' if obj.estimated_delivery else ''
            )
        return '-'
    tracking_info.short_description = 'Tracking'
    
    def action_buttons(self, obj):
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a class="button" href="{}" target="_blank" style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; text-decoration: none; font-size: 11px;">📄 Invoice</a>'
            '</div>',
            reverse('download_invoice', args=[obj.id])
        )
    action_buttons.short_description = 'Actions'
    
    actions = ['mark_as_pending', 'mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} orders marked as Pending.')
    mark_as_pending.short_description = "Mark as Pending"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} orders marked as Processing.')
    mark_as_processing.short_description = "Mark as Processing"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} orders marked as Shipped.')
    mark_as_shipped.short_description = "Mark as Shipped"
    
    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} orders marked as Delivered.')
    mark_as_delivered.short_description = "Mark as Delivered"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} orders marked as Cancelled.')
    mark_as_cancelled.short_description = "Mark as Cancelled"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'coupon')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_link', 'product', 'quantity', 'price_display', 'subtotal_display']
    list_filter = ['order__status']
    search_fields = ['order__id', 'product__name', 'order__user__username']
    readonly_fields = ['price']
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">#{}</a>', url, obj.order.id)
    order_link.short_description = 'Order #'
    
    def price_display(self, obj):
        return f"₹{obj.price}"
    price_display.short_description = 'Price'
    
    def subtotal_display(self, obj):
        return f"₹{obj.subtotal()}"
    subtotal_display.short_description = 'Subtotal'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type_badge', 'discount_value_display', 'minimum_order_amount', 'validity_period', 'usage_progress', 'is_active_badge']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code']
    readonly_fields = ['used_count', 'created_at']
    # REMOVED list_editable - since is_active is not in list_display directly
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'discount_type', 'discount_value', 'minimum_order_amount', 'max_discount_amount')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to', 'usage_limit', 'used_count', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def discount_type_badge(self, obj):
        if obj.discount_type == 'percentage':
            return format_html('<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px;">% OFF</span>')
        return format_html('<span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 12px;">FIXED</span>')
    discount_type_badge.short_description = 'Type'
    
    def discount_value_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        return f"₹{obj.discount_value}"
    discount_value_display.short_description = 'Value'
    
    def validity_period(self, obj):
        from django.utils import timezone
        now = timezone.now()
        if obj.valid_from <= now <= obj.valid_to:
            return format_html('<span style="color: #28a745;">✓ Active</span><br><small>Until {}</small>', obj.valid_to.strftime('%d %b %Y'))
        elif now < obj.valid_from:
            return format_html('<span style="color: #ffc107;">⏳ Upcoming</span><br><small>From {}</small>', obj.valid_from.strftime('%d %b %Y'))
        else:
            return format_html('<span style="color: #dc3545;">✗ Expired</span>')
    validity_period.short_description = 'Status'
    
    def usage_progress(self, obj):
        percent = (obj.used_count / obj.usage_limit) * 100 if obj.usage_limit > 0 else 0
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 10px; overflow: hidden;"><div style="width: {}%; background: #c8a96a; height: 6px;"></div></div><small>{}/{} used</small>',
            percent, obj.used_count, obj.usage_limit
        )
    usage_progress.short_description = 'Usage'
    
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px;">Active</span>')
        return format_html('<span style="background: #dc3545; color: white; padding: 2px 8px; border-radius: 12px;">Inactive</span>')
    is_active_badge.short_description = 'Active'


@admin.register(UsedCoupon)
class UsedCouponAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'coupon', 'order_link', 'used_at']
    list_filter = ['used_at']
    search_fields = ['user__username', 'coupon__code']
    readonly_fields = ['used_at']
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">#{}</a>', url, obj.order.id)
        return '-'
    order_link.short_description = 'Order'