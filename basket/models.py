from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from admin_sid.models import Product


# Create your models here.
class WishItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal_price(self):
        return self.quantity * self.product.price

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem)

    def get_total_price(self):
        return sum(item.subtotal_price() for item in self.items.all())

    def get_subtotal_price(self):
        subtotal = sum(item.subtotal_price() for item in self.items.all())
       
        return subtotal

    def get_shipping_price(self):
       
        return Decimal('11.5')

    def print_cart_items(self):
        for item in self.items.all():
            print(
                f"Product: {item.product.title}, Quantity: {item.quantity}, Price: {item.product.price}, Subtotal: {item.subtotal_price}"
            )

    def add_item_to_db(self, product, qty):
        cart_item, created = CartItem.objects.get_or_create(
            user=self.user, product=product, defaults={"quantity": qty}
        )

        if not created:
            cart_item.quantity += qty
            cart_item.save()

        self.items.add(cart_item) 

    def update_item_in_db(self, product, qty):
        cart_item = CartItem.objects.get(user=self.user, product=product)
        cart_item.quantity = qty
        cart_item.save()

    def delete_item_from_db(self, product):
        CartItem.objects.filter(user=self.user, product=product).delete()

    
    def clear_cart_in_db(self):
    
        self.items.all().delete()

    def save_to_db(self):
        self.save()

    def __iter__(self):
        return iter(self.items.all())
