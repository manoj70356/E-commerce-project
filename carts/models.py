from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.conf import settings
from django.contrib.auth.models import User
from store.models import Product, Variation
from accounts.models import Account
class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id


class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return str(self.product)


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders_user"
    )

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="orders_account"
    )

    order_number = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = (
                timezone.now().strftime('%Y%m%d') +
                "-" +
                str(uuid.uuid4()).split('-')[0]
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"
    


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    cart = models.ForeignKey('Cart', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)
    square_order_id = models.CharField(max_length=255, null=True, blank=True)

    checkout_id = models.CharField(max_length=255, null=True, blank=True)
    payment_id = models.CharField(max_length=255, unique=True, null=True, blank=True)  

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    coupon_code = models.CharField(max_length=50, null=True, blank=True)


    def __str__(self):
        return f"{self.payment_id or self.checkout_id} - {self.payment_status} - {self.amount}"

