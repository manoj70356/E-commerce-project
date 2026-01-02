from django.contrib import admin
from .models import Cart, CartItem, Order, Payment,Coupon,UsedCoupon


class CartAdmin(admin.ModelAdmin):
  list_display = ('cart_id', 'date_added')


class CouponAdmin(admin.ModelAdmin):
  list_display = ('code','discount_type','discount_value','min_cart_value','is_used')

class CartItemAdmin(admin.ModelAdmin):
  list_display = ('product', 'cart', 'quantity', 'is_active')


class PaymentAdmin(admin.ModelAdmin):
  list_display = ('payment_id', 'payment_status', 'amount', 'created_at')

class UsedCCCoupnAdmin(admin.ModelAdmin):
  list_display = ('user', 'coupon')

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order)
admin.site.register(Payment,PaymentAdmin)
admin.site.register(Coupon,CouponAdmin)
admin.site.register(UsedCoupon)


