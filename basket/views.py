from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from admin_sid.models import Product
from basket.models import CartItem, WishItem
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import Cart  # Import your Cart model
from basket.models import Cart
from .basket import Basket
from .models import Cart, CartItem
from django.views.decorators.http import require_POST


from decimal import Decimal

@login_required
def basket_summary(request):
    basket_instance = Basket(request)
    user = request.user
    cart, created = Cart.objects.get_or_create(user=user)

    cart = Cart.objects.get(user=request.user)

   
    cart_total = cart.get_total_price()
    subtotal = cart.get_subtotal_price()
    shipping_price = cart.get_shipping_price()
    
   
    total = subtotal + shipping_price

    
    context = {
        'cart': cart,
        'cart_total': cart_total,
        'subtotal': subtotal,
        'shipping_price': shipping_price,
        'total': total,
    }
    return render(request, "basket/summary.html", context)



@login_required
def basket_add(request):
    basket = Basket(request)
    if request.POST.get("action") == "post":
        product_id = int(request.POST.get("productid"))
        product_qty = int(request.POST.get("productqty"))
        product = get_object_or_404(Product, id=product_id)
        if product.stock >= product_qty:
            basket.add(product=product, qty=product_qty)
            basketqty = basket.__len__()
            response = JsonResponse({"qty": basketqty})
            return response


@login_required
@require_POST
def basket_delete(request, product_id):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        basket = Basket(request)
        product = Product.objects.get(id=product_id)
        basket.delete(product)

        basket_qty = len(basket)
        basket_subtotal = basket.get_subtotal_price()

        response_data = {
            "qty": basket_qty,
            "subtotal": basket_subtotal,
        }
        return JsonResponse(response_data)
    else:
        return JsonResponse({"error": "Invalid request"})


@login_required
def update_product_quantity(request, product_id):
    user = request.user
    cart, created = Cart.objects.get_or_create(user=user)
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        new_quantity = int(request.POST.get("productqty", 1))
        if new_quantity <= product.stock:
            cart.update_item_in_db(product, new_quantity)
            try:
                cart_item = cart.items.get(product=product)
                updated_qty = cart_item.quantity
            except CartItem.DoesNotExist:
                updated_qty = 0

            data = {
                "success": True,
                "qty": updated_qty,
                "productStock": product.stock,
                "subtotal": cart.get_subtotal_price(),
                "total": cart.get_total_price(),
                "productquantity": updated_qty,
            }
        else:
            data = {
                "success": False,
                "error": "Not enough stock available.",
            }

        return JsonResponse(data)

    return render(request, "basket/update_quantity.html", {"product": product})

@login_required
def add_to_wishlist(request, id):
    product = Product.objects.get(id=id)
    wish_item, created = WishItem.objects.get_or_create(
        user=request.user, product=product
    )
    if created:
        return redirect("home")
    else:
        return redirect("basket:wishlist")

@login_required
def wishlist(request):
   
    product = Product.objects.all()
    wish_items = WishItem.objects.filter(user=request.user)
    context = {
        "wish_items": wish_items,
        "product": product,
        
    }
    return render(request, "basket/wishlist.html", context)


def remove_from_wishlist(request, id):
    try:
        item_to_remove = WishItem.objects.get(id=id)
        item_to_remove.delete()
        return redirect("basket:wishlist")
    except WishItem.DoesNotExist:
        return redirect("basket:wishlist")
