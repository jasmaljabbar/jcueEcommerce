from django.urls import path

from . import views
from .views import BasketView
app_name = 'payment'


urlpatterns = [
    path('payment/address/', BasketView, name='basket_view'),
    path('order_placed/', views.order_placed, name='order_placed'),
    path('BasketView/', views.BasketView, name='BasketView'),
    path('address/', views.address, name='address'),
    path('add_address/', views.add_address, name='add_address'),    
    path('edit_address/<int:aid>', views.edit_address, name='edit_address'),    
    path('address_active/<int:aid>', views.address_active, name='address_active'),    
    path('edit_product_action', views.edit_product_action, name='edit_product_action'),    
    path('oreder_view', views.oreder_view, name='oreder_view'),    
    path('upi_paypal_com', views.upi_paypal_com, name='upi_paypal_com'),    
    path('order/<int:order_id>/',views.order_detail, name='order_detail'),  
    path('order/<int:order_id>/cancel/', views.order_cancel, name='cancel_order'), 
    path('delete_address/<int:aid>', views.delete_address, name='delete_address'),
    path('payment/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('return_order/<int:order_id>/', views.return_order, name='return_order'),
        
]
 