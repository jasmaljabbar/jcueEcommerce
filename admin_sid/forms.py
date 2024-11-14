
from django.core.validators import MinValueValidator
from django import forms
from .models import Coupon,Category,Banner,Product
from PIL import Image


class CouponForm(forms.ModelForm):
    discount_value = forms.DecimalField(
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )

    class Meta:
        model = Coupon
        fields = '__all__'
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expire_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_coupon_name(self):
        coupon_name = self.cleaned_data['coupon_name']
        if coupon_name and coupon_name.strip() == '':
            raise forms.ValidationError("Coupon name cannot be just spaces.")
        return coupon_name

class EditCouponForm(forms.ModelForm):
    discount_value = forms.DecimalField(
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )

    class Meta:
        model = Coupon
        fields = ['coupon_name', 'code', 'discount_type', 'discount_value', 'expire_date', 'coupon_type', 'min_purchase_amount']

    def clean_coupon_name(self):
        coupon_name = self.cleaned_data['coupon_name']
        if coupon_name and coupon_name.strip() == '':
            raise forms.ValidationError("Coupon name cannot be just spaces.")
        return coupon_name


class ReturnReasonForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea)




class AdminReturnResponseForm(forms.Form):
    response = forms.ChoiceField(choices=[('accepted', 'Accept'), ('rejected', 'Reject')],
                                 widget=forms.Select(attrs={'class': 'form-control'}),
                                 label='Admin Response')


class AddBannerForm(forms.Form):
    title = forms.CharField(label="Banner Title", max_length=100)
    image = forms.ImageField(label="Banner Image")
    link = forms.URLField(label="Banner Link", required=False)
    crop_width = forms.IntegerField(label="Crop Width", required=False)
    crop_height = forms.IntegerField(label="Crop Height", required=False)



    def clean_cropped_image(self):
        # Perform cropping if a new image is provided
        cropped_image = self.cleaned_data.get('cropped_image')
        if cropped_image:
            image = Image.open(cropped_image)
            # Perform cropping logic here
            # For example, you can use the crop function
            # image = image.crop((x, y, x + width, y + height))
            # Save the cropped image
            # image.save(cropped_image.path)
        return cropped_image



class EditBannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title', 'link', 'image']



class CategoryForm(forms.Form):
    new_category = forms.CharField(max_length=255, min_length=1, required=True)
    img = forms.ImageField(required=True)


class EditCategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['title', 'image']


class BrandForm(forms.Form):
    new_brand = forms.CharField(label='New Brand', max_length=100, required=True)


class EditBrandForm(forms.Form):
    edit_brand = forms.CharField(label='Edit Brand', max_length=100, required=True)



class ProductForm(forms.ModelForm):
    crop_width = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    crop_height = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Product
        fields = ['title', 'description', 'category', 'brand', 'stock', 'price', 'old_price', 'image1', 'image2', 'image3', 'image4']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        
        # Set required attribute to False for optional image fields
        self.fields['image2'].required = False
        self.fields['image3'].required = False
        self.fields['image4'].required = False

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_old_price(self):
        old_price = self.cleaned_data.get('old_price')
        if old_price and old_price <= 0:
            raise forms.ValidationError("Old Price must be greater than zero.")
        return old_price

    def clean(self):
        cleaned_data = super().clean()
        stock = cleaned_data.get('stock')
        price = cleaned_data.get('price')

        if stock is not None and stock < 0:
            self.add_error('stock', 'Stock cannot be negative.')

        if price is not None and price < 0:
            self.add_error('price', 'Price cannot be negative.')
