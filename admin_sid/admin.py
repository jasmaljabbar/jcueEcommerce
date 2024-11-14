from django.contrib import admin
from .models import Category, Brand, Product, Coupon, Banner, ProductOffer


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Banner)
admin.site.register(ProductOffer)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_name', 'code', 'discount_type', 'discount_value', 'expire_date', 'coupon_type', 'min_purchase_amount']
    search_fields = ['code', 'coupon_name']
    list_filter = ['discount_type', 'coupon_type']
