from django.db import models    
from django.contrib.auth.models import User

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=50, null=True, blank=True)
    address1 = models.CharField(max_length=250, null=True, blank=True)
    address2 = models.CharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    post_code = models.CharField(max_length=20, null=True, blank=True)
    flag = models.BooleanField(default=False)

    
    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.full_name}'s Address"
