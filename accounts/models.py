from django.db import models
from django.contrib.auth.models import User
from store.models import Product

class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favourites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')  # Ek user ek product ko ek baar favourite kar sakta hai
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class OTPVerification(models.Model):
    mobile = models.CharField(max_length=10, unique=True)
    otp = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"{self.mobile} - {self.otp}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at    