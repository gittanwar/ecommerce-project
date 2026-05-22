from django.urls import path
from . import views
from .views import send_otp, verify_otp


urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('toggle-favourite/<int:product_id>/', views.toggle_favourite, name='toggle_favourite'),
    path('favourites/', views.favourite_list, name='favourite_list'),
path('send-otp/', views.send_otp, name='send_otp'),

path('verify-otp/', views.verify_otp, name='verify_otp'),
path('resend-otp/', views.resend_otp, name='resend_otp'),
]