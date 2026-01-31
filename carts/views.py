from django.shortcuts import render, redirect,get_object_or_404
from store.models import Product, Variation
from .models import Cart,CartItem,Payment,Coupon,UsedCoupon
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
import requests
import uuid
import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.db import transaction
from django.contrib.auth import get_user_model
import time

def _cart_id(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key



@csrf_exempt
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product_variations = []

    if request.method == 'POST':
        for key, value in request.POST.items():
            try:
                variation = Variation.objects.get(
                    product=product,
                    variation_category__iexact=key,
                    variation_value__iexact=value
                )
                product_variations.append(variation)
            except Variation.DoesNotExist:
                pass
    cart_id = _cart_id(request)
    cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
    cart_items = CartItem.objects.filter(product=product, cart=cart, is_active=True)
    
    for item in cart_items:
        existing_variations = list(item.variations.all())
        if existing_variations == product_variations:
            item.quantity += 1
            item.save()
            break
    else:
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            is_active=True
        )
        if product_variations:
            cart_item.variations.set(product_variations)
            cart_item.save()

    return redirect('cart')

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)

    cart_item = CartItem.objects.filter(product=product, cart=cart).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart')



def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
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
    tax_rate = 18  

    discount = request.session.get('discount', 0)
    coupon_code = request.session.get('coupon_code')

    if discount > total:
        discount = total
    coupon_code = request.session.get("coupon_code")
    coupon = None
    if coupon_code:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.is_used:
                time.sleep(3)
                messages.error(request, "This coupon has already been used by another user. Please pay full amount.")
                del request.session['coupon_code']
                coupon_code = None

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
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

            total = sum(item.product.price * item.quantity for item in cart_items)
            if total < coupon.min_cart_value:
                messages.error(
                    request,
                    f"Minimum cart value must be {coupon.min_cart_value}"
                )
                return redirect('cart')
            if coupon.discount_type == "percent":
                discount = (coupon.discount_value / 100) * total
            else:
                discount = coupon.discount_value
            if discount > total:
                discount = total
            request.session['discount'] = discount
            request.session['coupon_code'] = coupon.code
            messages.success(request, "Coupon applied successfully")
        except Coupon.DoesNotExist:
            request.session['discount'] = 0
            request.session['coupon_code'] = None
            messages.error(request, "Invalid Coupon Code")
    return redirect('cart')


def remove_coupon(request):
    request.session['discount'] = 0
    request.session['coupon_code'] = None
    messages.success(request, "Coupon removed")
    return redirect('cart')



def order_success(request):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = None

    if cart:
        CartItem.objects.filter(cart=cart).delete()

    return render(request, 'order_success.html')


@login_required
def checkout(request):
    cart_id = _cart_id(request)
    cart = Cart.objects.get(cart_id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    total = sum(item.product.price * item.quantity for item in cart_items)

    coupon_code = request.session.get("coupon_code")
    coupon = None
    discount = 0

    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)

            if coupon.is_used:
                time.sleep(3)
                messages.error(request, "This coupon has already been used by another user. Please pay full amount.")
                del request.session['coupon_code']
                coupon_code = None
            else:
                if not coupon.is_valid(total):
                    time.sleep(2)
                    messages.error(request, "This coupon has already been used by another user. Please pay full amount.")
                    del request.session['coupon_code']
                    coupon_code = None
                else:
                    if coupon.discount_type == "amount":
                        discount = coupon.discount_value
                    else:
                        discount = total * (coupon.discount_value / 100)

        except Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon")
            del request.session['coupon_code']
            coupon_code = None

    if discount > total:
        discount = total

    total_after_discount = total - discount
    tax = total_after_discount * 0.18
    grand_total = total_after_discount + tax

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "total": total,
        "discount": round(discount, 2),
        "Tax": round(tax, 2),
        "grand_total": round(grand_total, 2),
        "coupon_code": coupon_code,
    }

    return render(request, "checkout.html", context)


@csrf_exempt
@login_required
def create_square_checkout(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id)
    cart_items = CartItem.objects.filter(cart=cart, is_active=True)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart")

    total = sum(item.product.price * item.quantity for item in cart_items)

    # Get coupon from session
    coupon_code = request.session.get("coupon_code")
    coupon = None
    discount = 0

    if coupon_code:
        coupon_obj = Coupon.objects.filter(code=coupon_code).first()
        if coupon_obj and coupon_obj.is_valid(total):
            coupon = coupon_obj
            # Calculate discount
            if coupon.discount_type == "amount":
                discount = coupon.discount_value
            else:
                discount = total * (coupon.discount_value / 100)
        else:
            messages.error(request, "Coupon not valid or expired")
            return redirect("cart")

    if discount > total:
        discount = total

    total_after_discount = total - discount
    tax_amount = total_after_discount * 0.18
    grand_total = total_after_discount + tax_amount

    # Prepare line items for Square checkout
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

    # Build checkout body
    body = {
        "idempotency_key": str(uuid.uuid4()),
        "order": {
            "location_id": SQUARE_LOCATION_ID,
            "line_items": line_items,
            "discounts": [
                {
                    "name": f"Coupon {coupon.code}",
                    "amount_money": {
                        "amount": int(discount * 100),
                        "currency": "USD"
                    }
                }
            ] if coupon else [],
            "taxes": [
                {
                    "name": "GST",
                    "percentage": "18"
                }
            ]
        },
        "checkout_options": {
            "redirect_url": request.build_absolute_uri("/cart/order-success/")
        }
    }

    response = requests.post(
        "https://connect.squareupsandbox.com/v2/online-checkout/payment-links",
        headers={
            "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=body
    )

    data = response.json()

    if response.status_code in (200, 201):
        Payment.objects.create(
            user=request.user,
            cart=cart,
            square_order_id=data["payment_link"]["order_id"],
            checkout_id=data["payment_link"]["id"],
            amount=grand_total,
            payment_status="pending",
            coupon_code=coupon.code if coupon else None
        )

        return redirect(data["payment_link"]["url"])

    return JsonResponse({"error": "Square checkout failed"}, status=400)


@csrf_exempt
def square_webhook(request):
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"ok": True})

    payment_data = data.get("data", {}).get("object", {}).get("payment", {})
    order_id = payment_data.get("order_id")
    status = payment_data.get("status")

    if not order_id:
        return JsonResponse({"ok": True})

    try:
        pay = Payment.objects.get(square_order_id=order_id)
    except Payment.DoesNotExist:
        return JsonResponse({"ok": True})

    # Update payment status
    if status in ["APPROVED", "COMPLETED"]:
        pay.payment_status = "completed"

        # Handle coupon usage
        if pay.coupon_code:
            try:
                coupon = Coupon.objects.get(code=pay.coupon_code)

                # Increment used_count
                coupon.used_count += 1
                # Deactivate if usage_limit reached
                if coupon.used_count >= coupon.usage_limit:
                    coupon.active = False
                coupon.save()

                # Create UsedCoupon record
                UsedCoupon.objects.get_or_create(user=pay.user, coupon=coupon)

            except Coupon.DoesNotExist:
                pass

        # Deactivate cart items
        if pay.cart:
            CartItem.objects.filter(cart=pay.cart).update(is_active=False)

    elif status in ["FAILED", "CANCELED"]:
        pay.payment_status = status.lower()

    pay.save()
    return JsonResponse({"status": "ok"})

