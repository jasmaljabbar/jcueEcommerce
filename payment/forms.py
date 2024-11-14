# forms.py
from django import forms
from orders.models import Order  # Make sure to import the Order model

class AddressForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'address1', 'phone', 'city', 'post_code']


# class CouponForm(forms.Form):
#     coupon_code = forms.CharField(max_length=50)