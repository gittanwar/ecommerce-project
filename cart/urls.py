from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    # path('add-to-cart-ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),  # Add this
    path('update-cart/<int:product_id>/', views.update_cart, name='update_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
]