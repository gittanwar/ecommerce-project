from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Favourite

# Register Favourite model
@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['user__username', 'product__name']
    raw_id_fields = ['user', 'product']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Favourite Information', {
            'fields': ('user', 'product')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# Optional: Customize User admin to show favourites
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'favourite_count']
    
    def favourite_count(self, obj):
        return Favourite.objects.filter(user=obj).count()
    favourite_count.short_description = 'Favourites'

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)