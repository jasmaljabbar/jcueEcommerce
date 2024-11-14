from decimal import Decimal
from django.contrib.auth.models import User
from django.conf import settings
from .models import CartItem, Cart




class Basket:
    def __init__(self, request, user=None):
        self.session = request.session
        self.user = user or request.user
        self.restore_session_data()

    def restore_session_data(self):
        if self.user.is_authenticated:
          
            cart, created = Cart.objects.get_or_create(user=self.user)
            self.user.cart = cart 
           

    
    def clear(self):
        if self.user.is_authenticated:
            self.user.cart.clear_cart_in_db()
        else:
            del self.session[settings.BASKET_SESSION_ID]
            self.session.modified = True

    def add(self, product, qty):
        product_id = str(product.id)
        if self.user.is_authenticated:
            self.user.cart.add_item_to_db(product, qty)
            
        else:
            if product_id in self.basket:
                self.basket[product_id]["qty"] += qty
            else:
                self.basket[product_id] = {"price": str(product.price), "qty": qty}
            self.save()
            

    def update(self, product, qty):
        product_id = str(product.id)
        if self.user.is_authenticated:
            self.user.cart.update_item_in_db(product, qty)
        else:
            if product_id in self.basket:
                self.basket[product_id]["qty"] = qty
            self.save()

    def delete(self, product):
        product_id = str(product.id)
        if self.user.is_authenticated:
            self.user.cart.delete_item_from_db(product)
        else:
            if product_id in self.basket:
                del self.basket[product_id]
                self.save()

    def save(self):
        if not self.user.is_authenticated:
            self.session[settings.BASKET_SESSION_ID] = self.basket
            self.session.modified = True

    def get_total_price(self):
        if self.user.is_authenticated:
            return self.user.cart.get_total_price()
        else:
            return sum(
                Decimal(item["price"]) * item["qty"] for item in self.basket.values()
            )

    def get_subtotal_price(self):
        if self.user.is_authenticated:
            return self.user.cart.get_subtotal_price()
        else:
            return sum(
                Decimal(item["price"]) * item["qty"] for item in self.basket.values()
            )




    def __iter__(self):
        if self.user.is_authenticated:
            return iter(self.user.cart.items.all())
        else:
            return iter(self.items)

    
    
    @property
    def items(self):
      
        if self.user:
            return CartItem.objects.filter(user=self.user)
        else:
        
            return []

    def __len__(self):
        return len(self.items)

