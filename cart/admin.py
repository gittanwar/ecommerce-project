from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'added_at']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_item_count', 'get_total', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def get_item_count(self, obj):
        return obj.get_item_count()
    get_item_count.short_description = 'Items'
    
    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = 'Total'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'get_total', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'product__name']
    
    def get_total(self, obj):
        return f"₹{obj.get_total()}"
    get_total.short_description = 'Subtotal'