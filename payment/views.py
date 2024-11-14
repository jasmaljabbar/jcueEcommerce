import json
from django.shortcuts import get_object_or_404
from admin_sid.models import Coupon, Product
from basket.basket import Basket
from orders.models import Order, OrderItem
from payment.models import Address
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import uuid
from django.db.models import Q
from datetime import datetime
from django.utils import timezone
from basket.models import Cart
from datetime import timedelta
from acount.models import  Wallet,Wallet_History
from admin_sid.forms import ReturnReasonForm
from orders.models import Order, ReturnRequest





def order_placed(request):
    return render(request, "payment/orderplaced.html")


def generate_order_key():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4().hex)[:6]  
    order_key = f"ORDER-{timestamp}-{unique_id}"
    return order_key

@login_required
def BasketView(request):
    request.session['discounted_total'] = 0
    billing_address = Address.objects.filter(user=request.user)
    cart, created = Cart.objects.get_or_create(user=request.user)

    wallet_balance = None
    coupons = []

    try:
        wallet_balance = Wallet.objects.get(user=request.user)
        user = request.user
        coupons = Coupon.objects.filter(
            Q(coupon_type='public') &
            Q(expire_date__gte=timezone.now()) &
            (Q(min_purchase_amount__lte=cart.get_total_price()) | Q(min_purchase_amount__isnull=True)) &
            ~Q(user=user)
        )
    except Wallet.DoesNotExist:
        Wallet.objects.create(user=request.user, balance=0)
        wallet_balance = Wallet.objects.get(user=request.user)

    shipping_price = cart.get_shipping_price()

    if request.method == "POST":
        custname = request.POST.get("custName", "")
        address1 = request.POST.get("custAdd", "")
        phone = request.POST.get("phone", "")
        state = request.POST.get("state", "")
        pincode = request.POST.get("pincode", "")
        addresses = Address.objects.all()

        if addresses:
            try:
                active_address = addresses.get(flag=True)
                active_address.flag = False
                active_address.save()
            except Address.DoesNotExist:
                pass

        if request.user.is_authenticated:
            user = request.user

            Address.objects.create(
                user=user,
                full_name=custname,
                address1=address1,
                phone=phone,
                city=state,
                post_code=pincode,
                flag=True,
            )

    return render(request, "payment/address.html", {
        "billing_address": billing_address,
        "shipping_price": shipping_price,
        "wallet_balance": wallet_balance,
        "coupons": coupons,
    })




@login_required
def address(request):
    try:
        billing_address = Address.objects.get(user=request.user, flag=True)

    except Address.DoesNotExist:
        
        error_data = {
            'error': 'No billing address found.',
            'detail': 'Please add a billing address.'
        }
        return JsonResponse({'success': True, 'error_data': error_data})
      

    cart, created = Cart.objects.get_or_create(user=request.user)
    shipping_price = cart.get_shipping_price()

    if request.method == "POST":
        basket = Basket(request)

        if billing_address:
            paymentmethod = request.POST.get("paymentMethod")
            total_paid = basket.get_total_price()
            order_key = generate_order_key()
            discounted_total = request.session.get('discounted_total')
            coupon_code = request.session.get('coupon-code')

            if discounted_total:
                total_paid = discounted_total
                coupon = Coupon.objects.get(code=coupon_code)

            for item in basket:  
                product = item.product
                if item.quantity > product.stock:
                    basket.clear()
                    billing_address = Address.objects.filter(user=request.user)
                    return render(
                        request,
                        "payment/address.html",
                        {
                            "message": f"Insufficient stock for {product.title}",
                            "billing_address": billing_address,
                            "shipping_price": shipping_price
                        },
                    )


            if paymentmethod == "cod" or paymentmethod == "wallet":
                if paymentmethod == "wallet":
                    user_wallet = Wallet.objects.get(user=request.user)

                    if user_wallet.balance >= total_paid:
                        user_wallet.balance -= total_paid
                        user_wallet.save()

                        wallet_history = Wallet_History.objects.create(
                            wallet=user_wallet,
                            transaction_type='debit',
                            amount=total_paid,
                        )

                order = Order.objects.create(
                    user=request.user,
                    full_name=billing_address.full_name,
                    address1=billing_address.address1,
                    address2=billing_address.address2,
                    city=billing_address.city,
                    phone=billing_address.phone,
                    post_code=billing_address.post_code,
                    total_paid=total_paid,
                    order_key=order_key,
                    billing_status=paymentmethod,
                )

                order_id = order.pk

                for item in basket.items.all():  
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                    product = item.product
                    product.stock -= item.quantity
                    product.best_sellers += item.quantity
                    product.save()
                try:
                    request.session['coupon-code'] = coupon_code
                    coupon = Coupon.objects.get(code=coupon_code)
                    coupon.user = request.user
                    coupon.save()
                    basket.clear()
                    return render(request, "payment/orderplaced.html")
                except:
                 
                    basket.clear()
                    return render(request, "payment/orderplaced.html")
            else:
               
                return render(request, "payment/UPI.html", {"discounted_total": discounted_total,
                                                             "shipping_price": shipping_price})
        else:
            return redirect('paymentBasketView')

    return redirect('payment:BasketView')








def upi_paypal_com(request):
    billing_address = get_object_or_404(Address, user=request.user, flag=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    shipping_price = cart.get_shipping_price()

    if request.method == "POST":
        basket = Basket(request)

        if billing_address:
            body = json.loads(request.body)
            paymentmethod = body.get("paymentmethod")
            total_paid = basket.get_total_price()
            order_key = generate_order_key()
            discounted_total = request.session.get('discounted_total')
            coupon_code = request.session.get('coupon-code')

            coupon = None
            if discounted_total and coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                except Coupon.DoesNotExist:
                    coupon = None
                    return HttpResponse("Coupon does not exist", status=400)
                    

            if coupon:
                total_paid = discounted_total

                for item in basket:  
                    product = item.product
                    if item.quantity > product.stock:
                        return render(
                            request,
                            "payment/address.html",
                            {
                                "message": f"Insufficient stock for {product.title}",
                                "billing_address": billing_address,
                                "shipping_price": shipping_price
                            },
                        )


            order = Order.objects.create(
                user=request.user,
                full_name=billing_address.full_name,
                address1=billing_address.address1,
                address2=billing_address.address2,
                city=billing_address.city,
                phone=billing_address.phone,
                post_code=billing_address.post_code,
                total_paid=total_paid,
                order_key=order_key,
                billing_status=paymentmethod,
            )

            order_id = order.pk

            for item in basket:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.subtotal_price(), 
                    quantity=item.quantity,
                )

                product = item.product
                product.stock -= item.quantity
                product.best_sellers += item.quantity
                product.save()
                

   
            basket.clear()

            request.session['coupon-code'] = coupon_code
            if coupon:
                coupon.user = request.user
                coupon.save()
               
            return JsonResponse("Payment completed", safe=False)

    return JsonResponse("Invalid request", safe=False)







def address_active(request, aid):
    billing_address = Address.objects.get(id=aid)
    act_address = Address.objects.filter(flag=True).first()
    if act_address:
        act_address.flag = False
        act_address.save()
    if billing_address:
        billing_address.flag = True
        billing_address.save()

    messages.success(request, "Address set to default")
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


def add_address(request):
    if request.user.is_authenticated:
        return render(request, "payment/home.html")
    else:
        return redirect("home")


def edit_address(request, aid):
    if request.user.is_authenticated:
        address = Address.objects.get(id=aid)
        return render(request, "payment/edit_address.html", {"address": address})
    else:
        return redirect("home")


def edit_product_action(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            id = request.POST.get("id")
            custname = request.POST.get("custName", "")
            address1 = request.POST.get("custAdd", "")
            phone = request.POST.get("phone", "")
            state = request.POST.get("state", "")
            pincode = request.POST.get("pincode", "")

            address = Address.objects.get(id=id)

            address.full_name = custname
            address.address1 = address1
            address.phone = phone
            address.city = state
            address.post_code = pincode

           
            address.save()
            billing_address = Address.objects.filter(user=request.user)
            return render(
                request, "payment/address.html", {"billing_address": billing_address}
            )
           
        else:
            return redirect("address")
    else:
        return redirect("home")


@login_required
def delete_address(request, aid):
    address = Address.objects.get(id=aid)
    if address.user != request.user:
        messages.error(request, "You don't have permission to delete this address.")
        return redirect("payment:address")
    address.delete()
    messages.success(request, "Address deleted successfully.")

    return redirect("payment:BasketView")


def oreder_view(request):
    orders = Order.objects.filter(user=request.user)
    order_statuses = {order.id: order.status for order in orders}
    return render(
        request,
        "payment/orders.html",
        {"orders": orders, "order_statuses": order_statuses},
    )


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    return render(
        request,
        "payment/order_detail.html",
        {"order": order, "order_items": order_items},
    )


def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        order_items = order.items.all()
        
        user_wallet = get_object_or_404(Wallet, user=order.user)
        for order_item in order_items:
            product = order_item.product
            product.stock += order_item.quantity
            product.best_sellers -= order_item.quantity
            if order.billing_status != 'cod':
                if order.discounted_total is None:
                    user_wallet.balance += order.total_paid
                else:
                  
                    user_wallet.balance += order.discounted_total
                wallet_history_entry = Wallet_History.objects.create(
                wallet=user_wallet,
                transaction_type='credit', 
                amount=order.total_paid if order.discounted_total is None else order.discounted_total
            )
                user_wallet.save()

            product.save()

        order.status = "canceled"
        order.save()

        return render(request, "payment/order_detail.html", {"order": order})

    return render(request, "payment/order_detail.html", {"order": order})









def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    return_request, created = ReturnRequest.objects.get_or_create(order=order)

    if request.method == 'POST':
        form = ReturnReasonForm(request.POST)
        if form.is_valid():
            
            return_request.user_reason = form.cleaned_data['reason']
            return_request.save()
            order.return_requested = True
            order.save()

            messages.success(request, 'Return request updated successfully.')
            return redirect('payment:order_detail', order_id=order.id)
        else:
            messages.error(request, 'Invalid form submission.')
    else:
    
        form = ReturnReasonForm(initial={'reason': return_request.user_reason if return_request else ''})

    return render(request, 'payment/order_detail.html', {'form': form, 'order': order})

 
