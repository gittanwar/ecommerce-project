from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('mock-payment/', views.mock_payment_view, name='mock_payment'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
    path('track-order/', views.track_order_by_number, name='track_order_by_number'),
    
]