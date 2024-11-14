from django.contrib import admin
from .models import User_profile,Wallet,Wallet_History

# Register your models here.

admin.site.register(User_profile)
admin.site.register(Wallet)
admin.site.register(Wallet_History)
