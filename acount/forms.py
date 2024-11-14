from django import forms
from .models import User_profile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User_profile
        fields = ['name','profil_photo', 'phone_number', 'address']

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']

        # Remove spaces from the phone number
        phone_number = phone_number.replace(" ", "")

        # Check if the phone number contains only digits and has a length of 10
        if not phone_number.isdigit() or len(phone_number) != 10:
            raise forms.ValidationError('Invalid phone number format. Please enter a 10-digit number without spaces.')

        return phone_number


class CouponApplyForm(forms.Form):
    coupon_code = forms.CharField(max_length=30)

