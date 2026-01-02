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
#     coupon = None  

#     if coupon_code:
#         try:
#             coupon = Coupon.objects.get(code=coupon_code)

#             if coupon.is_used:
#                 messages.error(request, "This coupon is already used")
#                 time.sleep(2.5)
#                 return redirect("cart")

#             if coupon.expiry_date and coupon.expiry_date < date.today():
#                 messages.error(request, "This coupon has expired")
#                 return redirect("cart")

#             if total < coupon.min_cart_value:
#                 messages.error(
#                     request,
#                     f"Minimum cart value must be {coupon.min_cart_value}"
#                 )
#                 return redirect("cart")

#             if coupon.discount_type == "amount":
#                 discount = float(coupon.discount_value)
#             elif coupon.discount_type == "percent":
#                 discount = total * (coupon.discount_value / 100)

#         except Coupon.DoesNotExist:
#             discount = 0
#             coupon = None

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

#         total_after_discount = total - discount
#         if total_after_discount < 0:
#             total_after_discount = 0

#         grand_total = total_after_discount + tax_amount

#         Payment.objects.create(
#             user=request.user if request.user.is_authenticated else None,
#             cart=cart_obj,
#             checkout_id=checkout_id,
#             square_order_id=result["payment_link"]["order_id"],
#             payment_id=None,
#             amount=grand_total,
#             payment_status="pending",
#             coupon_code=coupon_code
#         )

#         return redirect(checkout_url)

#     else:
#         print("Square API Error:", result)
#         return JsonResponse({"error": result}, status=400)






# @login_required
# def checkout(request):
#     cart_id = _cart_id(request)
#     cart_obj, created = Cart.objects.get_or_create(cart_id=cart_id)
#     cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)

#     total = sum(item.product.price * item.quantity for item in cart_items)

#     coupon_code = request.session.get('coupon_code')
#     discount = 0

#     if coupon_code:
#         try:
#             coupon = Coupon.objects.get(code=coupon_code)

            
#             if coupon.expiry_date and coupon.expiry_date < date.today():
#                 discount = 0


#             elif total < coupon.min_cart_value:
#                 discount = 0

#             else:
#                 if coupon.discount_type == 'amount':
#                     discount = coupon.discount_value

#                 elif coupon.discount_type == 'percent':
#                     discount = total * (coupon.discount_value / 100)

#         except Coupon.DoesNotExist:
#             discount = 0
#     total_after_discount = total - discount

#     if total_after_discount < 0:
#         total_after_discount = 0


#     tax_rate = 18
#     Tax = total_after_discount * (tax_rate / 100)


#     grand_total = total_after_discount + Tax

#     context = {
#         'cart': cart_obj,
#         'cart_items': cart_items,
#         'total': total,
#         'Tax': round(Tax, 0),
#         'discount': round(discount, 2),
#         'grand_total': round(grand_total, 2),
#         'coupon_code': coupon_code,
#     }

#     return render(request, 'checkout.html', context)






@login_required
def checkout(request):
    cart_id = _cart_id(request)
    cart_obj, created = Cart.objects.get_or_create(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart_obj, is_active=True)

    total = sum(item.product.price * item.quantity for item in cart_items)

    coupon_code = request.session.get('coupon_code')
    discount = 0

    # -------------------------------------------------------------
    # 🔥 STEP 1 — Final Coupon Validation Before Checkout Page Loads
    # -------------------------------------------------------------
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            # 1) Coupon already used → BLOCK checkout
            if coupon.is_used:
                messages.error(request, "This coupon is already used")
                return redirect("cart")

            # 2) Coupon expired check
            if coupon.expiry_date and coupon.expiry_date < date.today():
                messages.error(request, "This coupon has expired")
                return redirect("cart")

            # 3) Minimum cart value
            if total < coupon.min_cart_value:
                messages.error(
                    request,
                    f"Minimum cart value must be {coupon.min_cart_value}"
                )
                return redirect("cart")

            # 4) Valid coupon → calculate discount
            if coupon.discount_type == 'amount':
                discount = coupon.discount_value
            elif coupon.discount_type == 'percent':
                discount = total * (coupon.discount_value / 100)

        except Coupon.DoesNotExist:
            discount = 0
            messages.error(request, "Invalid coupon code")
            return redirect("cart")

    # -------------------------------------------------------------
    # 🔥 STEP 2 — Prevent discount > total
    # -------------------------------------------------------------
    if discount > total:
        discount = total

    total_after_discount = total - discount
    if total_after_discount < 0:
        total_after_discount = 0

    tax_rate = 18
    Tax = total_after_discount * (tax_rate / 100)

    grand_total = total_after_discount + Tax

    # -------------------------------------------------------------
    # Context Data
    # -------------------------------------------------------------
    context = {
        'cart': cart_obj,
        'cart_items': cart_items,
        'total': total,
        'Tax': round(Tax, 0),
        'discount': round(discount, 2),
        'grand_total': round(grand_total, 2),
        'coupon_code': coupon_code,
    }

    return render(request, 'checkout.html', context)


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
    coupon = None

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            # ❌ ALREADY USED
            if coupon.is_used:
                messages.error(request, "This coupon is already used.")
                return redirect("cart")

            # ❌ LOCKED BY ANOTHER USER
            if coupon.is_locked and coupon.locked_by != request.user:
                messages.error(request, "Another user is already using this coupon.")
                return redirect("cart")

            # 🔐 LOCK COUPON FOR THIS USER
            coupon.is_locked = True
            coupon.locked_by = request.user
            coupon.locked_at = timezone.now()
            coupon.save()

            # Validate
            if coupon.expiry_date and coupon.expiry_date < date.today():
                messages.error(request, "Coupon expired.")
                return redirect("cart")

            if total < coupon.min_cart_value:
                messages.error(request, f"Minimum cart value is {coupon.min_cart_value}")
                return redirect("cart")

            if coupon.discount_type == "amount":
                discount = float(coupon.discount_value)
            elif coupon.discount_type == "percent":
                discount = total * (coupon.discount_value / 100)

        except Coupon.DoesNotExist:
            discount = 0
            coupon = None

    if discount > total:
        discount = total

    tax_amount = total * 0.18

    # Build Square line items
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

    body = {
        "idempotency_key": str(uuid.uuid4()),
        "order": {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": line_items,
            "discounts": [
                {
                    "uid": "disc1",
                    "name": "Coupon Discount",
                    "amount_money": {
                        "amount": int(discount * 100),
                        "currency": "USD"
                    }
                }
            ],
            "taxes": [
                {
                    "uid": "tax1",
                    "name": "GST 18%",
                    "percentage": "18",
                }
            ]
        },
        "checkout_options": {
            "redirect_url": "http://127.0.0.1:8000/cart/order-success/"
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

    # PAYMENT LINK CREATED
    if response.status_code in (200, 201):

        checkout_id = result["payment_link"]["id"]

        Payment.objects.create(
            user=request.user,
            cart=cart_obj,
            checkout_id=checkout_id,
            square_order_id=result["payment_link"]["order_id"],
            payment_id=None,
            amount=total - discount + tax_amount,
            payment_status="pending",
            coupon_code=coupon_code
        )

        return redirect(result["payment_link"]["url"])

    else:
        # UNLOCK COUPON IF FAILED
        if coupon:
            coupon.is_locked = False
            coupon.locked_by = None
            coupon.save()

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
        status = payment_data.get("status")

        if not square_payment_id or not order_id:
            return JsonResponse({"ok": True})

        # ----------------------------------------------------------------
        # 1️⃣ Find payment entry
        # ----------------------------------------------------------------
        try:
            payment = Payment.objects.get(square_order_id=order_id)
        except Payment.DoesNotExist:
            print("NO PAYMENT MATCH FOUND IN DB")
            return JsonResponse({"ok": True})

        # Save payment_id
        payment.payment_id = square_payment_id

        # ----------------------------------------------------------------
        # 2️⃣ Handle payment success
        # ----------------------------------------------------------------
        if status in ["APPROVED", "COMPLETED"]:
            payment.payment_status = "completed"

            # ------------------------------------------------------------
            #  NEW: Mark Coupon as Used (FINAL VALIDATION)
            # ------------------------------------------------------------
            if payment.coupon_code: 
                try:
                    coupon = Coupon.objects.get(code=payment.coupon_code)

                    # only mark used if not already used
                    if not coupon.is_used:
                        coupon.is_used = True
                        coupon.save()
                        print("COUPON MARKED USED:", coupon.code)

                except Coupon.DoesNotExist:
                    print("COUPON NOT FOUND IN DB")

            # ------------------------------------------------------------
            # Clear cart items
            # ------------------------------------------------------------
            if payment.cart:
                CartItem.objects.filter(cart=payment.cart).update(is_active=False)

            if payment.user:
                CartItem.objects.filter(user=payment.user).update(is_active=False)

        # ----------------------------------------------------------------
        # 3️⃣ Failed or Canceled
        # ----------------------------------------------------------------
        elif status == "FAILED":
            payment.payment_status = "failed"
        elif status == "CANCELED":
            payment.payment_status = "canceled"

        payment.save()

        print("PAYMENT UPDATED:", payment.payment_status)

        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return JsonResponse({"error": str(e)}, status=400)
