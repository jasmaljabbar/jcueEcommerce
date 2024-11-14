import calendar
from django.shortcuts import get_object_or_404, render, redirect
from decimal import Decimal
from orders.models import Order, OrderItem
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Category 
from acount.models import  User_profile, Wallet,Wallet_History
from django.http import HttpResponse
from .models import Coupon,Banner, ProductOffer,Product
from django.db import IntegrityError
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractDay, ExtractMonth, ExtractYear
from .forms import CouponForm
from .forms import EditCouponForm
from .forms import ReturnReasonForm
from orders.models import Order, ReturnRequest
from django.db.models import Count, Avg
from django.db.models.functions import ExtractMonth
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from datetime import datetime, timedelta
from .forms import AddBannerForm,CategoryForm,BrandForm,EditBrandForm,EditBannerForm,EditCategoryForm,ProductForm  
from django.shortcuts import render, redirect
from PIL import Image


 





@login_required
def dashboard(request):
    active_users = User.objects.filter(is_active=True).exclude(is_superuser=True)
    total_active_users_count = active_users.count()
    products = Product.objects.filter(best_sellers__gt=0).order_by('-best_sellers')
    # Monthly sales data
    orders_month_report = (
        Order.objects.annotate(month=ExtractMonth("created"))
        .values("month")
        .annotate(monthly_orders_count=Count("id"))
        .annotate(monthly_sales=Sum("total_paid"))
        .values("month", "monthly_orders_count", "monthly_sales")
    )
    month = []
    total_orders_per_month = []
    total_sales_per_month = []

    for order in orders_month_report:
        month.append(calendar.month_name[order["month"]])
        total_orders_per_month.append(order["monthly_orders_count"])
        total_sales_per_month.append(order["monthly_sales"])

    current_month = timezone.now().month
    current_year = timezone.now().year
    orders_daily_report = (
        Order.objects.filter(billing_status='bank')  # Adjust the status filter as needed
        .filter(created__month=current_month, created__year=current_year)
        .annotate(day=ExtractDay("created"))
        .values("day")
        .annotate(daily_orders_count=Count("id"))
        .annotate(daily_sales=Sum("total_paid"))
        .values("day", "daily_orders_count", "daily_sales")
)

    day = []
    total_orders_per_day = []
    total_sales_per_day = []

    for order in orders_daily_report:
        day.append(order["day"])
        total_orders_per_day.append(order["daily_orders_count"])
        total_sales_per_day.append(order["daily_sales"])

    # Yearly sales count
    orders_year_report = (
        Order.objects.annotate(year=ExtractYear("created"))
        .values("year")
        .annotate(yearly_orders_count=Count("id"))
        .annotate(yearly_sales=Sum("total_paid"))
        .values("year", "yearly_orders_count", "yearly_sales")
    )
    year = []
    total_orders_per_year = []
    total_sales_per_year = []

    for order in orders_year_report:
        year.append(order["year"])
        total_orders_per_year.append(order["yearly_orders_count"])
        total_sales_per_year.append(order["yearly_sales"])

    orders = Order.objects.filter(Q(status='delivered')|Q(billing_status='bank'))
    balance = Order.objects.filter(status='delivered').aggregate(
        total_sales=Sum("total_paid")
    )
    
    
    product_data = []
    for product in products:
        total_quantity_sold = OrderItem.objects.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_income = total_quantity_sold * product.price
        product_data.append({
            'product': product,
            'total_quantity_sold': total_quantity_sold,
            'total_income': total_income,
        })
        
    
    total_income = Order.objects.filter(Q(billing_status='bank')|Q(status='delivered')).aggregate(total_income=Sum('total_paid'))['total_income'] or 0
    total_orders_count = Order.objects.count()
    order_items = Order.objects.aggregate(order_sum=Sum("total_paid"))
    context = {
        'product_data': product_data,
        "total_active_users_count": total_active_users_count,
        "total_orders_count": total_orders_count,
        "total_income": total_income,
        "orders": orders,
        "balance": balance,
        "sales": order_items,
        "month": month,
        "total_orders_per_month": total_orders_per_month,
        "total_sales_per_month": total_sales_per_month,
        "day": day,
        "total_orders_per_day": total_orders_per_day,
        "total_sales_per_day": total_sales_per_day,
        "year": year,
        "total_orders_per_year": total_orders_per_year,
        "total_sales_per_year": total_sales_per_year,
    }
    return render(request,'admin/dashboard.html',context)

def generate_pdf(request):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    orders = Order.objects.all()

   
    headers = ["Customer", "CONTACT", "DATE", "Total Paid"]
    col_widths = [pdf.stringWidth(header, "Helvetica", 25) for header in headers]


    col_widths[2] += 20  


    line_height = 34

    
    table_start_x = 100  
    y_position = 750

    for i, header in enumerate(headers):
        pdf.drawString(table_start_x + sum(col_widths[:i]), y_position - line_height, header)

    for order in orders:
        y_position -= line_height
        for i, value in enumerate([order.full_name, order.phone, order.created.strftime('%Y-%m-%d'), str(order.total_paid)]):
           
            if i == 2:
                pdf.setFont("Helvetica", 8)
                pdf.drawString(table_start_x + sum(col_widths[:i]), y_position - line_height, value)
                pdf.setFont("Helvetica", 10)  # Resetting the font size to the default
            else:
                pdf.drawString(table_start_x + sum(col_widths[:i]), y_position - line_height, str(value))

    pdf.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="orders.pdf"'
    return response

def banner(request):
    banners= Banner.objects.all()
    return render(request,'admin/show_banner.html',{'banners':banners})



def add_banner(request):
    if request.user.is_authenticated:
        form = AddBannerForm()
        return render(request, "admin/add_banner.html", {'form': form})
    else:
        return redirect("home")


def user_message(request):
    users_with_messages = User_profile.objects.exclude(message='')
    return render(request, 'admin/user_message.html', {'users': users_with_messages})


def view_message(request, user_id):
    user = get_object_or_404(User_profile, id=user_id)
    return render(request, 'admin/view_message.html', {'user': user})


from PIL import Image

def add_banner_action(request):
    if request.method == "POST":
        form = AddBannerForm(request.POST, request.FILES)  
        if form.is_valid():
            title = form.cleaned_data["title"]
            image = form.cleaned_data["image"]
            link = form.cleaned_data["link"]
            crop_width = form.cleaned_data["crop_width"]
            crop_height = form.cleaned_data["crop_height"]

            existing_banner = Banner.objects.filter(title=title)
            if existing_banner.exists():
                messages.error(request, "Banner with this title already exists.")
            else:
                banner = Banner(title=title, image=image, link=link)
                banner.save()

                # Process image with cropping
                if crop_width and crop_height:
                    image_path = banner.image.path
                    image = Image.open(image_path)
                    cropped_image = image.crop((0, 0, crop_width, crop_height))
                    cropped_image.save(image_path)

                messages.success(request, "Banner added successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")

    return redirect("banner")




def banner_action(request,bid):
    banner = Banner.objects.get(id=bid)
    if banner.is_active:
        banner.is_active = False
    else:
        banner.is_active = True
    banner.save()
    return redirect("banner")

def edit_banner(request, bid):
    if request.user.is_authenticated:
        banners = get_object_or_404(Banner, id=bid)
        form = EditBannerForm(instance=banners)
        return render(request, "admin/edit_banner.html", {'banners': banners, 'form': form})
    else:
        return redirect("home")

def edt_banner_action(request):
    if request.method == "POST":
        form = EditBannerForm(request.POST, request.FILES)

        if form.is_valid():
            banner_id = request.POST.get("brand_id", None)
            
            if banner_id is not None and banner_id.isdigit():
                banner_id = int(banner_id)
                
                new_banner_name = form.cleaned_data['title']
                new_banner_link = form.cleaned_data['link']
                new_banner_img = form.cleaned_data['image']

                banner = get_object_or_404(Banner, id=banner_id) 
                banner.title = new_banner_name
                banner.link = new_banner_link
                banner.image = new_banner_img
                banner.save()

                return redirect("banner")

    else:
        form = EditBannerForm()

    return render(request, "admin/edit_banner.html", {'form': form})


@never_cache
def show_category(request):
    if request.user.is_authenticated:
        category = Category.objects.all()
        return render(request, "admin/show_category.html", {"category": category})
    else:
        return redirect("home")

@never_cache
def add_category(request):
    if request.user.is_authenticated:
        form = CategoryForm()
        return render(request, "admin/add_category.html", {'form': form})
    else:
        return redirect("home")


def add_category_action(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)

        if form.is_valid():
            new_category = form.cleaned_data['new_category']
            img = form.cleaned_data['img']

            # Check if a category with the same title already exists (case-insensitive)
            existing_category = Category.objects.filter(title__iexact=new_category)

            if existing_category.exists():
                messages.error(request, "Category already exists")
                return redirect("add_category")
            else:
                category = Category(title=new_category, image=img)
                category.save()

            return redirect("show_category")
        else:
            messages.error(request, "Invalid form submission. Please check the form.")
            return redirect("add_category")

    return redirect("show_category")


@never_cache
def edit_category(request, cid):
    if request.user.is_authenticated:
        category = Category.objects.get(id=cid)
        form = EditCategoryForm(instance=category)
        return render(request, "admin/edit_category.html", {"category": category, "form": form})
    else:
        return redirect("home")

from django.contrib import messages

def edt_category_action(request):
    if request.method == "POST":
        form = EditCategoryForm(request.POST, request.FILES)

        if form.is_valid():
            category_id = request.POST.get("category_id")
            new_category_name = form.cleaned_data['title']
            new_category_img = form.cleaned_data['image']

            
            existing_category = Category.objects.filter(title__iexact=new_category_name).exclude(id=category_id)

            if existing_category.exists():
                messages.error(request, "Category already exists")
                return redirect("add_category")

            category = get_object_or_404(Category, id=category_id)

            category.title = new_category_name

            if new_category_img:
                category.image = new_category_img

            category.save()

            return redirect("show_category")
    else:
        form = EditCategoryForm()

    return render(request, "admin/edit_category.html", {'form': form})


@never_cache
def show_brand(request):
    if request.user.is_authenticated:
        brand = Brand.objects.all()
        return render(request, "admin/show_brand.html", {"brand": brand})
    else:
        return redirect("home")

@never_cache
def add_brand(request):
    if request.user.is_authenticated:
        form = BrandForm()
        return render(request, "admin/add_brand.html", {'form': form})
    else:
        return redirect("home")

def add_brand_action(request):
    if request.method == "POST":
        form = BrandForm(request.POST)

        if form.is_valid():
            new_brand = form.cleaned_data['new_brand']
            existing_brand = Brand.objects.filter(title=new_brand)

            if existing_brand.exists():
                messages.error(request, "Brand already exists")
                return redirect("add_brand")
            else:
                brand = Brand(title=new_brand)
                brand.save()
            return redirect("show_brand")
    else:
        form = BrandForm()

    return render(request, "admin/add_brand.html", {'form': form})

@never_cache
def edit_brand(request, bid):
    if request.user.is_authenticated:
        brand = Brand.objects.get(id=bid)
        form = EditBrandForm(initial={'edit_brand': brand.title})
        return render(request, "admin/edit_brand.html", {"brand": brand, "form": form})
    else:
        return redirect("home")

def edt_brand_action(request):
    if request.method == "POST":
        form = EditBrandForm(request.POST)

        if form.is_valid():
            id = request.POST.get("id")
            name = form.cleaned_data['edit_brand']
            existing_brand = Brand.objects.filter(title=name)

            if existing_brand.exists():
                messages.error(request, "Brand already exists")
                return redirect("edit_brand", bid=id)
            else:
                brand = Brand.objects.get(id=id)
                brand.title = name
                brand.save()
                return redirect("show_brand")
    else:
        form = EditBrandForm()

    return render(request, "admin/edit_brand.html", {"form": form})

@never_cache
def show_product(request):
    if request.user.is_authenticated:
        products = Product.objects.all()
        return render(request, "admin/show_product.html", {"products": products})
    else:
        return redirect("home")

@never_cache
def admin_view_product(request, uid):
    if request.user.is_authenticated:
        products = Product.objects.get(id=uid)
        return render(request, "admin/view_products.html", {"products": products})
    else:
        return redirect("home")

@never_cache
def edit_product(request, uid):
    if request.user.is_authenticated:
        product = Product.objects.get(id=uid)
        category = Category.objects.all()
        brand = Brand.objects.all()
        return render(
            request,
            "admin/edit_product.html",
            {"product": product, "category": category, "brand": brand},
        )
    else:
        return redirect("home")

def edit_product_action(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            id = request.POST.get("id")
            name = request.POST.get("name")
            description = request.POST.get("description")
            category = request.POST.get("category")
            brand = request.POST.get("brand")
            stock = request.POST.get("stock")
            price1 = request.POST.get("price1")
            price2 = request.POST.get("price2")
            img1 = request.FILES.get("img1")
            img2 = request.FILES.get("img2")
            img3 = request.FILES.get("img3")
            img4 = request.FILES.get("img4")

            # Validate title, stock, price1, and price2
            if not name.strip():
                messages.error(request, 'Title cannot be empty or contain only spaces.')
                return redirect("show_product")

            try:
                stock = int(stock)
                if stock < 0:
                    stock = 0
            except ValueError:
                stock = 0

            try:
                price1 = float(price1)
                if price1 < 0:
                    price1 = 0
            except ValueError:
                price1 = 0

            try:
                price2 = float(price2)
                if price2 < 0:
                    price2 = 0
            except ValueError:
                price2 = 0

            # Update the product with validated values
            product = Product.objects.get(id=id)
            product.title = name
            product.description = description
            product.stock = stock
            product.price = price1
            product.old_price = price2
            product.category_id = category
            product.brand_id = brand

            # Update product images if provided
            if img1 is not None:
                product.image1 = img1
            if img2 is not None:
                product.image2 = img2
            if img3 is not None:
                product.image3 = img3
            if img4 is not None:
                product.image4 = img4

            # Save the updated product
            product.save()

            messages.success(request, 'Product updated successfully.')
            return redirect("show_product")
        else:
            messages.error(request, 'Invalid request. Please try again.')
            return redirect("show_product")
    else:
        return redirect("home")
    
def handle_non_negative(value):
    try:     
        float_value = float(value)
        return max(0, round(float_value))
    except ValueError:
        return 0



def add_product(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()

               
                crop_width = form.cleaned_data.get('crop_width')
                crop_height = form.cleaned_data.get('crop_height')

                if crop_width and crop_height:
                    product = Product.objects.latest('id')  # Adjust this based on your model's primary key
                    for field in ['image1', 'image2', 'image3', 'image4']:
                        image_field = getattr(product, field)
                        if image_field:
                            image = Image.open(image_field.path)
                            cropped_image = image.crop((0, 0, crop_width, crop_height))
                            cropped_image.save(image_field.path)

                return redirect("show_product")
        else:
            form = ProductForm()

        category = Category.objects.all()
        brand = Brand.objects.all()
        context = {"category": category, "brand": brand, "form": form}
        
        if not form.is_valid():
            context['form_errors'] = form.errors

        return render(request, "admin/add_product.html", context)
    else:
        return redirect("home")


@never_cache
def show_user(request):
    if request.user.is_authenticated:
        users = User.objects.all().exclude(is_superuser=True)
        return render(request, "admin/show_user.html", {"users": users})
    else:
        return redirect("home")

def customeraction(request, uid):
    if request.user.is_authenticated:
        customer = User.objects.get(id=uid)
        if customer.is_active:
            customer.is_active = False
        else:
            customer.is_active = True
        customer.save()
        return redirect("show_user")
    else:
        return redirect("home")

def product_action(request, uid):
    product = Product.objects.get(id=uid)
    if product.active:
        product.active = False
    else:
        product.active = True
    product.save()
    return redirect("show_product")

def category_action(request, cid):
    category = Category.objects.get(id=cid)
    if category.active:
        category.active = False
    else:
        category.active = True
    category.save()
    return redirect("show_category")

def brand_action(request, bid):
    brand = Brand.objects.get(id=bid)
    if brand.active:
        brand.active = False
    else:
        brand.active = True
    brand.save()
    return redirect("show_brand")

def order(request):
    orders = Order.objects.all()
    if request.method == "POST":
        order_id = request.POST.get("orderId")
        selected_status = request.POST.get("status")
        order_item = Order.objects.get(id=order_id)
        order_item.status = selected_status
        order_item.save()
        messages.success(request, "succesfully updated")
    return render(request, "admin/admin_order.html", {"orders": orders})


def order_details(request, oid):
    orders = Order.objects.get(id=oid)
    return_request = ReturnRequest.objects.filter(order=orders).first()
    return render(request, "admin/order_details.html", {"orders": orders, 'return_request': return_request})


def order_rejected(request, order_id):
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

        order.status = "rejected"
        order.save()

        return render(request, "admin/order_details.html", {"order": order})

    return render(request, "admin/order_details.html", {"order": order})


def category_offer(request):
    category_data = Category.objects.all()
    offer_data = ProductOffer.objects.all()

    return render(request, 'admin/category_offer.html', {'categoryData': category_data, 'offerData': offer_data})

@require_POST
@csrf_protect
@csrf_exempt
def add_category_offer(request):
    try:
        category_id = request.POST.get('category')
        discount_type = request.POST.get('discountType')
        percentage = request.POST.get('percentage')
        start_date_str = request.POST.get('startDate')
        end_date_str = request.POST.get('endDate')

        category = Category.objects.get(id=category_id)

        start_date_naive = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date_naive = datetime.strptime(end_date_str, '%Y-%m-%d')

        start_date = timezone.make_aware(start_date_naive, timezone.get_current_timezone())
        end_date = timezone.make_aware(end_date_naive, timezone.get_current_timezone())

        existing_offer = ProductOffer.objects.filter(category=category, expire_date__gt=timezone.now()).first()
        if existing_offer:
            raise ValueError("An active offer already exists for this category. Please update the existing offer or choose a different category.")

        offer = ProductOffer(
            category=category,
            discount_type=discount_type,
            discount_value=percentage,
            start_date=start_date,
            expire_date=end_date
        )
        if discount_type != 'fixed' and int(percentage) > 99:
             raise ValueError("Percentage is up to 99")
        if not offer.is_valid_for_category():
            raise ValueError("Category offer is not valid.")

        with transaction.atomic():
            # Create the category offer
            offer.save()

           
            products = Product.objects.filter(category=category)
            
            for product in products:
                if discount_type == 'fixed':
                    product.discount_price = product.old_price
                    product.old_price = product.price
                    percentage = Decimal(str(percentage))  # Convert to Decimal
                    product.price = product.price - percentage
                else:
                    product.discount_price = product.old_price
                    product.old_price = product.price
                    percentage = Decimal(str(percentage))  # Convert to Decimal
                    product.price = product.price - (percentage / 100) * product.price
                
                product.has_offer = True
                product.save()

        response_data = {'success': True, 'message': 'Category offer added successfully'}
    except ObjectDoesNotExist as e:
       
        response_data = {'success': False, 'message': 'Invalid category ID'}
    except IntegrityError:
        response_data = {'success': False, 'message': 'An offer for this category already exists'}
    except ValueError as e:
        response_data = {'success': False, 'message': str(e)}
    except Exception as e:
        response_data = {'success': False, 'message': str(e)}

    return JsonResponse(response_data)

@require_http_methods(['DELETE'])
@csrf_exempt
def delete_category_offer(request, offer_id):
    try:
        offer = ProductOffer.objects.get(id=offer_id)
        offer.delete()
        products = Product.objects.filter(category=offer.category)
        for product in products:
                product.price = product.old_price
                product.old_price = product.discount_price
                product.discount_price = 0
                product.has_offer = False 
                product.save()

        response_data = {'success': True, 'message': 'Category offer deleted successfully'}
    except ObjectDoesNotExist:
        response_data = {'success': False, 'message': 'Invalid offer ID'}
    except Exception as e:
        response_data = {'success': False, 'message': str(e)}

    return JsonResponse(response_data)

def coupon_admin(request):
    coupons = Coupon.objects.all()
    return render(request, "admin/coupon_admin.html", {"coupons": coupons})

def manage_coupons(request):
    coupons = Coupon.objects.all()
    form = CouponForm()

    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_coupons')
        else:
            messages.error(request, ' coupon is not valid.')
            return redirect('manage_coupons')
            

    return render(request, 'admin/manage_coupons.html', {'coupons': coupons, 'form': form})

def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    form = CouponForm(instance=coupon)

    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Coupon edited successfully')
            return redirect('manage_coupons')
        else:
            messages.error(request, 'Error editing coupon. Please correct the errors.')
            return redirect('manage_coupons')

    return render(request, 'admin/edit_coupon.html', {'form': form, 'coupon': coupon})

def delete_coupon(request, coupon_id):
    ("Inside delete_coupon view") 
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        coupon.delete()
        return redirect('manage_coupons')

    return HttpResponse("Invalid request. Use a POST request to delete a coupon.")

def handle_return_request(request, request_id):
    return_request = get_object_or_404(ReturnRequest, id=request_id)

    if request.method == 'POST':
        response = request.POST.get('response')
        if response in ['accepted', 'rejected']:
            return_request.admin_response = response
            return_request.save()

           
            order = return_request.order
            if response == 'accepted':
                order.status = 'returned'
                order.save()

                
                user_wallet = get_object_or_404(Wallet, user=order.user)
                if order.discounted_total is None:
                    transaction_amount = order.total_paid
                else:
                    transaction_amount = order.discounted_total

                wallet_history_entry = Wallet_History.objects.create(
                    wallet=user_wallet,
                    transaction_type='credit',  
                    amount=transaction_amount
                )
                
                
                user_wallet.balance += transaction_amount
                user_wallet.save()

                messages.success(request, 'Return request accepted. Wallet balance updated successfully.')
            elif response == 'rejected':
                messages.success(request, 'Return request rejected.')

            return redirect(reverse('order_details', args=[order.id]))

        else:
            messages.error(request, 'Invalid response.')
    else:
        return render(request, 'admin/order_details.html', {'return_request': return_request})

def return_requests_admin(request):
    return_requests = ReturnRequest.objects.filter(admin_response__isnull=True)
    return render(request, 'admin/order_details.html', {'return_requests': return_requests})


