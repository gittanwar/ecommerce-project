# cart/context_processors.py
from .views import get_cart_count

def cart_count(request):
    return {
        'cart_count': get_cart_count(request)
    }