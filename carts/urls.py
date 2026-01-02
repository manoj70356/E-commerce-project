
from django.urls import path
from . import views
urlpatterns = [
    path('', views.cart, name='cart'),  
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:product_id>', views.remove_cart, name='remove_cart'),
    path('remove_cart_item/<int:product_id>', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('create_square_checkout/<int:cart_id>/', views.create_square_checkout, name='create_square_checkout'),
    path('webhook/', views.square_webhook, name='square-webhook'),
    path('order-success/', views.order_success, name='order_success'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),

    
]
