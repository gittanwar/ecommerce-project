from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('contact/', views.contact_view, name='contact'),
    path('shop/', views.shop_view, name='shop'),
    path('about/', views.about_view, name='about'),
    path('quick-view/<int:product_id>/', views.quick_view, name='quick_view'),
    path('add-to-cart-ajax/<int:product_id>/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('get-products-ajax/', views.get_products_ajax, name='get_products_ajax'),
    path('check-favourite/<int:product_id>/', views.check_favourite, name='check_favourite'),
    path('toggle-favourite-detail/<int:product_id>/', views.toggle_favourite_detail, name='toggle_favourite_detail'),
    path('subscribe-newsletter/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('contact-submit/', views.contact_submit, name='contact_submit'),

]