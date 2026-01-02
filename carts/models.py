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
    
# import uuid
# from django.db import models
# from django.conf import settings
# from django.utils import timezone
# import random
# import string

# def generate_coupon_code(length=12):
#     while True:
#         code = ''.join(random.choices(string.ascii_uppercase, k=length))
#         if not Coupon.objects.filter(code=code).exists():
#             return code

# class Coupon(models.Model):
#     DISCOUNT_TYPE = (
#         ('amount', 'Fixed Amount'),
#         ('percent', 'Percentage'),
#     )

#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     code = models.CharField(max_length=50, unique=True, default=generate_coupon_code)
#     description = models.CharField(max_length=255, blank=True)
#     discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, default='percent')
#     discount_value = models.DecimalField(max_digits=10, decimal_places=2)

#     min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     usage_limit = models.PositiveIntegerField(default=1)
#     used_count = models.PositiveIntegerField(default=0)

#     active = models.BooleanField(default=True)
#     valid_from = models.DateTimeField()
#     valid_to = models.DateTimeField()

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     # Square discount ID kept optional
#     square_discount_id = models.CharField(max_length=255, null=True, blank=True)

#     def is_valid(self, cart_total):
#         now = timezone.now()
#         if not self.active:
#             return False
#         if self.used_count >= self.usage_limit:
#             return False
#         if self.valid_from > now or self.valid_to < now:
#             return False
#         if cart_total < self.min_cart_value:
#             return False
#         return True

#     def __str__(self):
#         return f"{self.code} ({self.discount_type})"

# class UsedCoupon(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
#     used_on = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ("user", "coupon")

#     def __str__(self):
#         return f"{self.user} - {self.coupon.code}"

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string
from square.client import Client as Square
from square.environment import SquareEnvironment

def generate_coupon_code(length=12):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=length))
        if not Coupon.objects.filter(code=code).exists():
            return code

class Coupon(models.Model):
    DISCOUNT_TYPE = (
        ('amount', 'Fixed Amount'),
        ('percent', 'Percentage'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, default=generate_coupon_code)
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

    min_cart_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Square discount ID
    square_discount_id = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Save model first
        super().save(*args, **kwargs)

        # Square Catalog API call to create discount if not exists
        if not self.square_discount_id:
            try:
                client = Square(
                    environment=SquareEnvironment.SANDBOX,  # PRODUCTION me change karna
                    token=settings.SQUARE_ACCESS_TOKEN
                )
                discount_object = {
                    "id": f"#coupon-{self.code}",
                    "type": "DISCOUNT",
                    "discount_data": {
                        "name": self.code,
                        "discount_type": "FIXED_AMOUNT" if self.discount_type == "amount" else "FIXED_PERCENTAGE",
                        "percentage": str(self.discount_value) if self.discount_type == "percent" else None,
                        "amount_money": {
                            "amount": int(self.discount_value * 100),
                            "currency": "CAD",
                        } if self.discount_type == "amount" else None,
                        "scope": "ORDER",
                    }
                }
                response = client.catalog.batch_upsert(
                    batches=[{"objects": [discount_object]}],
                    idempotency_key=str(uuid.uuid4())
                )
                if response.errors is None:
                    self.square_discount_id = response.objects[0].id
                    super().save(update_fields=["square_discount_id"])
                else:
                    print("Square API Error:", response.errors)
            except Exception as e:
                print("Square API Exception:", e)

    def is_valid(self, cart_total):
        now = timezone.now()
        if not self.active:
            return False
        if self.used_count >= self.usage_limit:
            return False
        if self.valid_from > now or self.valid_to < now:
            return False
        if cart_total < self.min_cart_value:
            return False
        return True

    def __str__(self):
        return f"{self.code} ({self.discount_type})"


class UsedCoupon(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "coupon")

    def __str__(self):
        return f"{self.user} - {self.coupon.code}"



# class Coupon(models.Model):
#     DISCOUNT_TYPE = (
#         ('amount', 'Amount'),
#         ('percent', 'Percentage'),
#     )

#     code = models.CharField(max_length=50, unique=True)
#     discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE)
#     discount_value = models.IntegerField()
#     min_cart_value = models.IntegerField(default=0)

#     is_used = models.BooleanField(default=False)
#     expiry_date = models.DateField(null=True, blank=True)
#     square_discount_id = models.CharField(max_length=255, null=True, blank=True)

#     def is_valid(self, cart_total):
#         if self.is_used:
#             return False

#         if self.expiry_date and self.expiry_date < timezone.now().date():
#             return False

#         if cart_total < self.min_cart_value:
#             return False

#         return True

#     def __str__(self):
#         return self.code



# class UsedCoupon(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
#     used_on = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ("user", "coupon")

#     def __str__(self):
#         return f"{self.user} - {self.coupon.code}"




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

