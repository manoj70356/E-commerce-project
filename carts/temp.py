def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()

        try:
            coupon = Coupon.objects.get(code=code)

            if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                messages.error(request, "This coupon has expired")
                return redirect('cart')

            # Cart total
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            total = sum(item.product.price * item.quantity for item in cart_items)

            # Minimum check
            if total < coupon.min_cart_value:
                messages.error(request, f"Minimum cart value must be {coupon.min_cart_value}")
                return redirect('cart')

            #  CHECK: Is coupon used by THIS user?
            if request.user.is_authenticated:
                already_used = UsedCoupon.objects.filter(
                    user=request.user,
                    coupon=coupon
                ).exists()

                if already_used:
                    messages.error(request, "You already used this coupon")
                    return redirect('cart')

            # Calculate discount
            if coupon.discount_type == "percent":
                discount = (coupon.discount_value / 100) * total
            else:
                discount = coupon.discount_value

            if discount > total:
                discount = total

            # Save to session
            request.session['discount'] = float(discount)
            request.session['coupon_code'] = coupon.code

            #  save in UsedCoupon table
            if request.user.is_authenticated:
                UsedCoupon.objects.create(
                    user=request.user,
                    coupon=coupon
                )

            messages.success(request, "Coupon applied successfully")

        except Coupon.DoesNotExist:
            request.session['discount'] = 0
            messages.error(request, "Invalid Coupon Code")

    return redirect('cart')



@csrf_exempt
def cart(request):
    cart_id = _cart_id(request)
    cart, created = Cart.objects.get_or_create(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    if not cart_items.exists():
        request.session['discount'] = 0
        request.session['coupon_code'] = None

    total = sum(item.product.price * item.quantity for item in cart_items)

    discount = request.session.get('discount', 0)
    coupon_code = request.session.get('coupon_code')

    if discount > total:
        discount = total
    
    tax =  [100 / (100 + 18)]
    grand_total = total - discount
    used_coupons = []
    if request.user.is_authenticated:
        used_coupons = UsedCoupon.objects.filter(user=request.user)

    from django.utils import timezone
    active_coupon = Coupon.objects.filter(expiry_date__gte=timezone.now().date(), is_used=False).first()

    context = {
        'cart': cart,
        'cart_total': total,
        'used_coupons': used_coupons,
        'cart_items': cart_items,
        'total': total - discount,
        'discount': discount,
        'grand_total': grand_total,
        'coupon_code': coupon_code,

        'active_coupon': active_coupon,
    }
    return render(request, 'cart.html', context)


@csrf_exempt
def create_square_checkout(request, cart_id):
    try:
        cart_obj = Cart.objects.get(id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)
    except Cart.DoesNotExist:
        return JsonResponse({"error": "Cart not found"}, status=400)

    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    total = sum(item.product.price * item.quantity for item in cart_items)

    coupon_code = request.session.get("coupon_code")
    discount = 0

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if coupon.expiry_date and coupon.expiry_date < date.today():
                discount = 0
            elif total < coupon.min_cart_value:
                discount = 0
            else:
                if coupon.discount_type == "amount":
                    discount = float(coupon.discount_value)
                elif coupon.discount_type == "percent":
                    discount = total * (coupon.discount_value / 100)

        except Coupon.DoesNotExist:
            discount = 0

    if discount > total:
        discount = total

 
    tax_rate = 18
    tax_amount = total * (tax_rate / 100)


    line_items = []
    for item in cart_items:
        line_items.append({
            "name": item.product.product_name,
            "quantity": str(item.quantity),
            "base_price_money": {
                "amount": int(item.product.price * 100),
                "currency": "USD"
            }
        })

    # ---------------------------
    # 3. CREATE BODY ✅
    # ---------------------------
    body = {
        "idempotency_key": str(uuid.uuid4()),
        "order": {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": line_items,

            "taxes": [
                {
                    "uid": "tax1",
                    "name": "GST 18%",
                    "percentage": "18",
                    "scope": "ORDER"
                }
            ],

            "discounts": [
                {
                    "uid": "disc1",
                    "name": "Coupon Discount",
                    "amount_money": {
                        "amount": int(discount * 100),
                        "currency": "USD"
                    },
                    "scope": "ORDER"
                }
            ]
        },

        "checkout_options": {
            "redirect_url": "http://127.0.0.1:8000/cart/order-success/",
            "ask_for_shipping_address": False,
        }
    }

    # ---------------------------
    # 4. SEND TO SQUARE ✅
    # ---------------------------
    response = requests.post(
        "https://connect.squareupsandbox.com/v2/online-checkout/payment-links",
        headers={
            "Square-Version": "2024-04-17",  
            "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=body
    )

    result = response.json()

    if response.status_code in [200, 201]:
        checkout_id = result["payment_link"]["id"]
        checkout_url = result["payment_link"]["url"]

        total_after_discount = total - discount
        if total_after_discount < 0:
            total_after_discount = 0

        grand_total = total_after_discount + tax_amount

        Payment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cart=cart_obj,
            checkout_id=checkout_id,
            square_order_id=result["payment_link"]["order_id"],
            payment_id=None,
            amount=grand_total,
            payment_status='pending'
        )

        return redirect(checkout_url)

    else:
        print("Square API Error:", result)
        return JsonResponse({"error": result}, status=400)


payment.payment_id = payment_data.get("id")

if payment_data.get("status") in ["APPROVED", "COMPLETED"]:
    payment.payment_status = "completed"
    payment.save()

    # Cart clear
    if payment.cart:
        CartItem.objects.filter(cart=payment.cart).update(is_active=False)

    if payment.user:
        CartItem.objects.filter(user=payment.user).update(is_active=False)

    # ✅ Coupon only after successful payment
    coupon_code = request.session.get("coupon_code")

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if not coupon.is_used:
                coupon.is_used = True
                coupon.save()

            # Session se bhi hata do
            request.session['coupon_code'] = None
            request.session['discount'] = 0

        except Coupon.DoesNotExist:
            pass

    request.session['cart_id'] = None



#### ---------------------------- Real Logic ------------------------------- ###

# @csrf_exempt
# def square_webhook(request):
#     if request.method != 'POST':
#         return HttpResponse(status=405)

#     try:
#         ## Receive Webhook JSON Data From Square
#         data = json.loads(request.body)
#         # print("SQUARE WEBHOOK RECEIVED:", data)
        
#         ## Extract Important Values
#         payment_data = data.get("data", {}).get("object", {}).get("payment", {})
#         square_payment_id = payment_data.get("id")
#         square_status = payment_data.get("status")
#         order_id = payment_data.get("order_id")

#          ## If Payment ID or Order ID missing → ignore
#         if not square_payment_id or not order_id:
#             return JsonResponse({"ok": True})
#         try:
#             ## Find the Payment Record in Your Database
#             payment = Payment.objects.get(square_order_id=payment_data.get("order_id"))
#         except Payment.DoesNotExist:
#             print("NO PAYMENT MATCH FOUND IN DB")
#             return JsonResponse({"ok": True})

#         payment.payment_id = payment_data.get("id")
#         if payment_data.get("status") in ["APPROVED", "COMPLETED"]:
#             payment.payment_status = "completed"

#             if payment.cart:
#                 CartItem.objects.filter(cart=payment.cart).update(is_active=False)

#             if payment.user:
#                 CartItem.objects.filter(user=payment.user).update(is_active=False)
      
#             request.session['cart_id'] = None

#         elif payment_data.get("status") == "FAILED":
#             payment.payment_status = "failed"
#         elif payment_data.get("status") == "CANCELED":
#             payment.payment_status = "canceled"
#         payment.save()

#         print("PAYMENT SUCCESSFULLY:", payment.payment_status)

#         return JsonResponse({"status": "ok"}, status=200)

#     except Exception as e:
#         print("WEBHOOK ERROR:", str(e))
#         return JsonResponse({"error": str(e)}, status=400)






# @csrf_exempt
# def create_square_checkout(request, cart_id):
#     try:
#         cart_obj = Cart.objects.get(id=cart_id)
#         cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)
#     except Cart.DoesNotExist:
#         return JsonResponse({"error": "Cart not found"}, status=400)

#     if not cart_items.exists():
#         return JsonResponse({"error": "Cart is empty"}, status=400)
    
#     total = sum(item.product.price * item.quantity for item in cart_items)

#     coupon_code = request.session.get("coupon_code")
#     discount = 0
#     if coupon_code:
#         try:
#             coupon = Coupon.objects.get(code = coupon_code)

#             if coupon.expiry_date and coupon.expiry_date < date.today():
#                 discount = 0
#             elif total < coupon.min_cart_value:
#                 discount = 0
#             else:
#                 if coupon.discount_type == "amount":
#                     discount = float(coupon.discount_value)
#                 elif coupon.discount_type == "percent":
#                     discount = total * (coupon.discount_value / 100)

#         except Coupon.DoesNotExist:
#             discount = 0


#     if discount > total:
#         discount = total

#     tax_rate = 18
#     tax_amount = total * (tax_rate / 100)            

#     line_items = []
#     for item in cart_items:
#         line_items.append({
#             "name": item.product.product_name,
#             "quantity": str(item.quantity),
#             "base_price_money": {
#                 "amount": int(item.product.price * 100),
#                 "currency": "USD"
#             }
#         })

#     body = {
#         "idempotency_key": str(uuid.uuid4()),
#         "order": {
#             "location_id": SQUARE_LOCATION_ID,
#             "line_items": line_items,
            

#             "taxes": [
#                 {
#                     "uid": "tax1",
#                     "name": "GST 18%",
#                     "percentage": "18",
#                     "scope": "ORDER"
#                 }
#             ],

#             "discounts": [
#                 {
#                     "uid": "disc1",
#                     "name": "Coupon Discount",
#                     "amount_money": {
#                         "amount": int(discount * 100),
#                         "currency": "USD"
#                     },
#                     "scope": "ORDER"
#                 }
#             ]
#         },
#         "checkout_options": {
#             "redirect_url": "http://127.0.0.1:8000/cart/order-success/",
#             "ask_for_shipping_address": False,
#         }
#     }


#     response = requests.post(
#         "https://connect.squareupsandbox.com/v2/online-checkout/payment-links",
#         headers={
#             "Square-Version": "2025-11-15",
#             "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
#             "Content-Type": "application/json"
#         },
#         json=body
#     )

#     result = response.json()

#     if response.status_code in [200, 201]:
#         checkout_id = result["payment_link"]["id"]
#         checkout_url = result["payment_link"]["url"]
#         order_id = result["payment_link"]["order_id"]

#         total_after_discount = total - discount
#         if total_after_discount < 0:
#             total_after_discount = 0

#         grand_total = total_after_discount + tax_amount

#         # Create Payment entry with checkout_id
#         Payment.objects.create(
#             user=request.user if request.user.is_authenticated else None,
#             cart=cart_obj,
#             checkout_id=checkout_id,
#             square_order_id=result["payment_link"]["order_id"],
#             payment_id=None,  
#             amount=grand_total,
#             payment_status='pending'
#         )

#         return redirect(checkout_url)

#     else:
#         print("Square API Error:", result)
#         return JsonResponse({"error": result}, status=400)





<script>
    localStorage.removeItem("applied_coupon");
    localStorage.removeItem("discount");
</script>

<h2>Payment Successful ✅</h2>



<script>
    const savedCoupon = localStorage.getItem("applied_coupon");
    if (savedCoupon && document.querySelector('input[name="coupon_code"]')) {
        document.querySelector('input[name="coupon_code"]').value = savedCoupon;
    }
</script>





from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone

from .models import Cart, CartItem, Coupon
from .utils import _cart_id   # agar different file mein ho

# ------------------ CART VIEW ------------------
@csrf_exempt
def cart(request):
    cart_id = _cart_id(request)
    cart, created = Cart.objects.get_or_create(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    # ✅ IF CART IS EMPTY → CLEAR & UNLOCK COUPON
    if not cart_items.exists():
        coupon_code = request.session.get('coupon_code')

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                coupon.is_locked = False
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        request.session['discount'] = 0
        request.session['coupon_code'] = None

    total = sum(item.product.price * item.quantity for item in cart_items)
    tax_rate = 18

    discount = request.session.get('discount', 0)
    coupon_code = request.session.get('coupon_code')

    if discount > total:
        discount = total

    total_after_discount = total - discount
    tax = total_after_discount * (tax_rate / 100)
    grand_total = total_after_discount + tax

    active_coupon = Coupon.objects.filter(
        expiry_date__gte=timezone.now().date(),
        is_used=False
    ).first()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': round(total, 2),
        'discount': round(discount, 2),
        'Tax': round(tax, 2),
        'grand_total': round(grand_total, 2),
        'coupon_code': coupon_code,
        'active_coupon': active_coupon,
    }

    return render(request, 'cart.html', context)


# ------------------ APPLY COUPON ------------------
def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()

        try:
            coupon = Coupon.objects.get(code=code)

            if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                messages.error(request, "This coupon has expired")
                return redirect('cart')

            if coupon.is_used:
                messages.error(request, "This coupon is already used")
                return redirect('cart')

            if coupon.is_locked:
                messages.error(request, "This coupon is currently in use by another user")
                return redirect('cart')

            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            if not cart_items.exists():
                messages.error(request, "Your cart is empty")
                return redirect('cart')

            total = sum(item.product.price * item.quantity for item in cart_items)

            if total < coupon.min_cart_value:
                messages.error(request, f"Minimum cart value must be {coupon.min_cart_value}")
                return redirect('cart')

            if coupon.discount_type == "percent":
                discount = (coupon.discount_value / 100) * total
            else:
                discount = coupon.discount_value

            if discount > total:
                discount = total

            # ✅ Save in session
            request.session['discount'] = float(discount)
            request.session['coupon_code'] = coupon.code

            # ✅ LOCK coupon
            coupon.is_locked = True
            coupon.save()

            messages.success(request, "Coupon applied successfully!")

        except Coupon.DoesNotExist:
            request.session['discount'] = 0
            request.session['coupon_code'] = None
            messages.error(request, "Invalid Coupon Code")

    return redirect('cart')


# ------------------ REMOVE SINGLE ITEM ------------------
def remove_cart_item(request, item_id):
    try:
        cart_id = _cart_id(request)
        cart = Cart.objects.get(cart_id=cart_id)

        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()

        # ✅ check if cart became empty
        if not CartItem.objects.filter(cart=cart, is_active=True).exists():
            coupon_code = request.session.get('coupon_code')

            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    coupon.is_locked = False
                    coupon.save()
                except Coupon.DoesNotExist:
                    pass

            request.session['discount'] = 0
            request.session['coupon_code'] = None

    except Exception as e:
        print(e)

    return redirect('cart')


# ------------------ CLEAR FULL CART ------------------
def clear_cart(request):
    cart_id = _cart_id(request)
    cart = Cart.objects.get(cart_id=cart_id)

    CartItem.objects.filter(cart=cart).delete()

    coupon_code = request.session.get('coupon_code')

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            coupon.is_locked = False
            coupon.save()
        except Coupon.DoesNotExist:
            pass

    request.session['discount'] = 0
    request.session['coupon_code'] = None

    return redirect('cart')








<-- THis code is test purpose-->



@login_required(login_url='loginview')
def create_square_order_view(request, plan_id):
    code = request.GET.get('coupon_code')
    
    url = f"{MAYA_BASE_URL}/connectivity/v1/product/{plan_id}"
    r = requests.get(url, headers=headers)
    plan = r.json()['product']

    valid_or_obj = coupon_validation(code,plan)
    if code and coupon_validation(plan_id):
        coupon = valid_or_obj
    else : coupon = None

    client = Square(
        environment=SquareEnvironment.SANDBOX,  # Switch to PRODUCTION in live
        token=os.getenv('SQUARE_ACCESS_TOKEN')
    )

    result = client.locations.list()
    location = result.locations[0]
    print('lcoationid : ',str(location))
    #converting in to cents
    price = int(round(float(plan.get('rrp_cad')) * 100))
    try:
        response = client.checkout.payment_links.create(
                order={
                    "location_id": location.id,
                    "line_items": [
                        {
                            "name": plan.get('name'),
                            "quantity": "1",
                            "base_price_money": {
                                "amount":price ,
                                "currency": "CAD"
                            },
                            "metadata": {
                                "user_id": str(request.user.id),
                                "plan_id": str(plan_id)
                            }
                        }
                    ],
                    "discounts": [
                {
                    "catalog_object_id":coupon.square_discount_id ,  # discount catalog object id from coupon
                    "scope": "ORDER"  # or "LINE_ITEM" depending on applicability
                }
            ]
                },
                checkout_options= {
                    "redirect_url": request.build_absolute_uri("/payment-success/")
                }
            ) if coupon else client.checkout.payment_links.create(
                order={
                    "location_id": location.id,
                    "line_items": [
                        {
                            "name": plan.get('name'),
                            "quantity": "1",
                            "base_price_money": {
                                "amount":price ,
                                "currency": "CAD"
                            },
                            "metadata": {
                                "user_id": str(request.user.id),
                                "plan_id": str(plan_id)
                            }
                        }
                    ]
                },
                checkout_options= {
                    "redirect_url": request.build_absolute_uri("/payment-success/")
                }
            )
        checkout_url = response.payment_link.url  # square.link URL
        Order.objects.create(
            id=response.payment_link.order_id,
            customer=request.user,  # adjust to your Customer relation
            status="pending",
            payment_link=checkout_url,
            plan_uid=plan_id,
            plan_country_iso3=plan.get('countries_enabled')[0],
            plan_data_quota_bytes=plan.get('data_quota_bytes'),
            plan_validity_days=plan.get('validity_days'),
            plan_policy_name=plan.get('policy_name'),
            plan_policy_id=plan.get('policy_id'),
            plan_rrp_usd_cents=price,
            coupon=request.GET.get('coupon_code')
        )

        return redirect(checkout_url)

    except ApiError as e:
        # Optional: Log errors or notify you
        print("Square Checkout API Error:", e.errors)
        return redirect("/payment-error/")
    

    class Coupon(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True,default=generate_coupon_code)    # Unique coupon code
    description = models.CharField(max_length=255, blank=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[("percent", "Percent"), ("fixed", "Fixed Amount")],
        default="percent"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)      # Uses per coupon
    used_count = models.PositiveIntegerField(default=0)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    square_discount_id = models.CharField(max_length=50,null=True,blank=True)

    def save(self, *args, **kwargs):
        # Call super save to persist the model first
        super().save(*args, **kwargs)

        if not self.square_discount_id:
            # Prepare discount data for Square Catalog API
            try:
                client = Square(
                    environment=SquareEnvironment.SANDBOX,  # Switch to PRODUCTION in live
                    token=settings.SQUARE_ACCESS_TOKEN
                )
                discount_object = {
                    "id": f"#coupon-{self.code}",  # temporary client-side ID required for creating new objects
                    "type": "DISCOUNT",
                    "discount_data": {
                        "name": self.code,
                        "discount_type": "FIXED_AMOUNT" if self.discount_type == "fixed" else "FIXED_PERCENTAGE",
                        "percentage": str(self.discount_value) if self.discount_type == "percent" else None,
                        "amount_money": {
                            "amount": int(self.discount_value * 100),  # Convert dollars to cents
                            "currency": "CAD",  # adapt currency if needed
                        } if self.discount_type == "fixed" else None,
                        "scope": "ORDER",  # or "LINE_ITEM" if applicable               
                    }
                }
                response = client.catalog.batch_upsert(batches=[{"objects": [discount_object]}],idempotency_key=str(uuid.uuid4()))
                if response.errors == None:
                    # Save the created discount object ID returned from Square
                    self.square_discount_id = response.objects[0].id
                    super().save(update_fields=["square_discount_id"])
                else:
                    print("Square API Error:", response.errors)
            except Exception as e:
                print("Square API Exception:", e)

    def is_valid(self):
        now = timezone.now()
        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            (self.used_count < self.usage_limit)
        )

    def __str__(self):
        return f"{self.code} ({self.discount_type})"
    


@csrf_exempt
def create_square_checkout(request, cart_id):
    try:
        cart_obj = Cart.objects.get(id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)
    except Cart.DoesNotExist:
        return JsonResponse({"error": "Cart not found"}, status=400)

    if not cart_items.exists():
        return JsonResponse({"error": "Cart is empty"}, status=400)

    total = sum(item.product.price * item.quantity for item in cart_items)

    coupon_code = request.session.get("coupon_code")
    coupon_obj = None
    discount_amount = 0
    square_discount_id = None

    # ======================
    # COUPON VALIDATION
    # ======================
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(
                code=coupon_code,
                is_used=False
            )

            # user level usage check
            if request.user.is_authenticated:
                if UsedCoupon.objects.filter(user=request.user, coupon=coupon_obj).exists():
                    coupon_obj = None

            if coupon_obj:
                # expiry
                if coupon_obj.expiry_date and coupon_obj.expiry_date < date.today():
                    coupon_obj = None

                # min value
                elif total < coupon_obj.min_cart_value:
                    coupon_obj = None

                else:
                    square_discount_id = coupon_obj.square_discount_id

                    if coupon_obj.discount_type == "amount":
                        discount_amount = float(coupon_obj.discount_value)
                    else:
                        discount_amount = total * (coupon_obj.discount_value / 100)

        except Coupon.DoesNotExist:
            coupon_obj = None

    if discount_amount > total:
        discount_amount = total

    tax_rate = 18
    tax_amount = total * (tax_rate / 100)

    line_items = [
        {
            "name": item.product.product_name,
            "quantity": str(item.quantity),
            "base_price_money": {
                "amount": int(item.product.price * 100),
                "currency": "USD"
            }
        }
        for item in cart_items
    ]

    # ORDER STRUCTURE
    order_body = {
        "location_id": SQUARE_LOCATION_ID,
        "line_items": line_items,
        "taxes": [
            {
                "uid": "gst",
                "name": "GST 18%",
                "percentage": "18",
                "scope": "ORDER"
            }
        ]
    }

    # APPLY SQUARE CATALOG DISCOUNT
    if coupon_obj and square_discount_id:
        order_body["discounts"] = [
            {
                "catalog_object_id": square_discount_id,
                "scope": "ORDER"
            }
        ]

    body = {
        "idempotency_key": str(uuid.uuid4()),
        "order": order_body,
        "checkout_options": {
            "redirect_url": "http://127.0.0.1:8000/cart/order-success/",
            "ask_for_shipping_address": False,
        }
    }

    response = requests.post(
        "https://connect.squareupsandbox.com/v2/online-checkout/payment-links",
        headers={
            "Square-Version": "2025-11-15",
            "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=body
    )

    result = response.json()

    if response.status_code in [200, 201]:
        checkout_id = result["payment_link"]["id"]
        checkout_url = result["payment_link"]["url"]
        order_id = result["payment_link"]["order_id"]

        total_after_discount = max(total - discount_amount, 0)
        grand_total = total_after_discount + tax_amount

        Payment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cart=cart_obj,
            checkout_id=checkout_id,
            square_order_id=order_id,
            payment_id=None,
            amount=grand_total,
            payment_status='pending',
            coupon=coupon_obj
        )

        return redirect(checkout_url)

    else:
        print("Square API Error:", result)
        return JsonResponse({"error": result}, status=400)

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()

        try:
            coupon = Coupon.objects.get(code=code)

            if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                messages.error(request, "This coupon has expired")
                return redirect('cart')

            if coupon.is_used:
                messages.error(request, "This coupon is already used")
                return redirect('cart')

            # user already used before?
            if request.user.is_authenticated:
                if UsedCoupon.objects.filter(user=request.user, coupon=coupon).exists():
                    messages.error(request, "You have already used this coupon before")
                    return redirect('cart')

            # cart
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            total = sum(item.product.price * item.quantity for item in cart_items)

            if total < coupon.min_cart_value:
                messages.error(request, f"Minimum cart value must be {coupon.min_cart_value}")
                return redirect('cart')

            if coupon.discount_type == "percent":
                discount = (coupon.discount_value / 100) * total
            else:
                discount = coupon.discount_value

            if discount > total:
                discount = total

            request.session['discount'] = float(discount)
            request.session['coupon_code'] = coupon.code

            messages.success(request, "Coupon applied successfully!")

        except Coupon.DoesNotExist:
            request.session['discount'] = 0
            request.session['coupon_code'] = ''
            messages.error(request, "Invalid Coupon Code")

    return redirect('cart')

@csrf_exempt
def square_webhook(request):
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
        payment_data = data.get("data", {}).get("object", {}).get("payment", {})
        square_payment_id = payment_data.get("id")
        order_id = payment_data.get("order_id")

        if not square_payment_id or not order_id:
            return JsonResponse({"ok": True})

        try:
            payment = Payment.objects.get(square_order_id=order_id)
        except Payment.DoesNotExist:
            print("NO PAYMENT MATCH FOUND IN DB")
            return JsonResponse({"ok": True})

        payment.payment_id = square_payment_id

        status = payment_data.get("status")

        if status in ["APPROVED", "COMPLETED"]:
            payment.payment_status = "completed"

            if payment.cart:
                CartItem.objects.filter(cart=payment.cart).update(is_active=False)

            if payment.user:
                CartItem.objects.filter(user=payment.user).update(is_active=False)

            # mark coupon used permanently
            if payment.coupon and not payment.coupon.is_used:
                coupon = payment.coupon
                coupon.is_used = True
                coupon.save()
                UsedCoupon.objects.create(user=payment.user, coupon=coupon)

        elif status == "FAILED":
            payment.payment_status = "failed"

        elif status == "CANCELED":
            payment.payment_status = "canceled"

        payment.save()
        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=400)
