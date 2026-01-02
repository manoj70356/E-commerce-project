def coupon_validation(code, plan):
    if not code:
        return None

    from .models import Coupon

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return None

    cart_total = int(float(plan.get('rrp_cad')))

    if not coupon.is_valid(cart_total):
        return None

    return coupon
