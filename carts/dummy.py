

SQUARE_ACCESS_TOKEN = "EAAAl3EM5vkiookhz6mYTzwjF6xHRKaOVEifyUgEvyj9ji5hLIbzgD41bIPHtgeJ"
SQUARE_LOCATION_ID = "LAQ5K4DF5DT25"
CURRENCY = os.getenv("CURRENCY", "USD") 



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
    coupon = None  # store coupon object

    if coupon_code:
        try:
            # Only apply if not used globally and not used by this user
            coupon = Coupon.objects.get(code=coupon_code, is_used=False)
            if request.user.is_authenticated:
                if UsedCoupon.objects.filter(user=request.user, coupon=coupon).exists():
                    coupon = None
                    discount = 0

            if coupon:
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

        total_after_discount = max(total - discount, 0)
        grand_total = total_after_discount + tax_amount

        # Create Payment entry with applied coupon
        Payment.objects.create(
            user=request.user if request.user.is_authenticated else None,
            cart=cart_obj,
            checkout_id=checkout_id,
            square_order_id=order_id,
            payment_id=None,
            amount=grand_total,
            payment_status='pending',
            coupon=coupon
        )

        return redirect(checkout_url)
    else:
        print("Square API Error:", result)
        return JsonResponse({"error": result}, status=400)


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

        if payment_data.get("status") in ["APPROVED", "COMPLETED"]:
            payment.payment_status = "completed"

            if payment.cart:
                CartItem.objects.filter(cart=payment.cart).update(is_active=False)

            if payment.user:
                CartItem.objects.filter(user=payment.user).update(is_active=False)

                # MARK COUPON AS USED
                if payment.coupon and not payment.coupon.is_used:
                    coupon = payment.coupon
                    coupon.is_used = True
                    coupon.save()
                    UsedCoupon.objects.create(user=payment.user, coupon=coupon)

        elif payment_data.get("status") == "FAILED":
            payment.payment_status = "failed"
        elif payment_data.get("status") == "CANCELED":
            payment.payment_status = "canceled"

        payment.save()
        print("PAYMENT SUCCESSFULLY:", payment.payment_status)

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=400)



def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()

        try:
            coupon = Coupon.objects.get(code=code)

            # Expiry check
            if coupon.expiry_date and coupon.expiry_date < timezone.now().date():
                messages.error(request, "This coupon has expired")
                return redirect('cart')

            # Already used
            if coupon.is_used:
                messages.error(request, "This coupon is already used")
                return redirect('cart')

            # Already locked (being used by someone)
            if coupon.is_locked:
                messages.error(request, "This coupon is currently in use by another user")
                return redirect('cart')

            # Cart total
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            total = sum(item.product.price * item.quantity for item in cart_items)

            # Minimum cart value
            if total < coupon.min_cart_value:
                messages.error(request, f"Minimum cart value must be {coupon.min_cart_value}")
                return redirect('cart')

            # Calculate discount
            if coupon.discount_type == "percent":
                discount = (coupon.discount_value / 100) * total
            else:
                discount = coupon.discount_value

            if discount > total:
                discount = total

            # ✅ Save in session
            request.session['discount'] = float(discount)
            request.session['coupon_code'] = coupon.code

            # ✅ LOCK the coupon
            coupon.is_locked = True
            coupon.save()

            messages.success(request, "Coupon applied successfully and locked!")

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

        if payment_data.get("status") in ["APPROVED", "COMPLETED"]:
            payment.payment_status = "completed"

            if payment.cart:
                CartItem.objects.filter(cart=payment.cart).update(is_active=False)

            if payment.user:
                CartItem.objects.filter(user=payment.user).update(is_active=False)

                # ✅ COUPON FINAL USE
                if payment.coupon:
                    coupon = payment.coupon

                    if not coupon.is_used:
                        coupon.is_used = True

                    coupon.is_locked = False   # ✅ UNLOCK now
                    coupon.save()

                    UsedCoupon.objects.create(user=payment.user, coupon=coupon)

        elif payment_data.get("status") == "FAILED":
            payment.payment_status = "failed"

            # if payment failed → unlock coupon
            if payment.coupon:
                coupon = payment.coupon
                coupon.is_locked = False
                coupon.save()

        elif payment_data.get("status") == "CANCELED":
            payment.payment_status = "canceled"

            if payment.coupon:
                coupon = payment.coupon
                coupon.is_locked = False
                coupon.save()

        payment.save()
        print("PAYMENT STATUS:", payment.payment_status)

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=400)
