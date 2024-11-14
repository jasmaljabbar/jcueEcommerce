from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('add/',views.add, name='add'),
    path('dashboard/',views.dashboard, name='dashboard'),
    
]
