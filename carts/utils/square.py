import uuid
import requests
from django.conf import settings


SQUARE_ACCESS_TOKEN = "EAAAl3EM5vkiookhz6mYTzwjF6xHRKaOVEifyUgEvyj9ji5hLIbzgD41bIPHtgeJ"
SQUARE_LOCATION_ID = "LAQ5K4DF5DT25"



def create_square_discount(coupon):
    """
    Create a Discount inside Square Catalog automatically.
    """

    body = {
        "idempotency_key": str(uuid.uuid4()),
        "object": {
            "type": "DISCOUNT",
            "id": f"#{coupon.code}",
            "discount_data": {
                "name": coupon.code,
            }
        }
    }

    if coupon.discount_type == "amount":
        body["object"]["discount_data"]["discount_type"] = "FIXED_AMOUNT"
        body["object"]["discount_data"]["amount_money"] = {
            "amount": int(coupon.discount_value * 100),
            "currency": "USD"
        }
    else:
        body["object"]["discount_data"]["discount_type"] = "FIXED_PERCENTAGE"
        body["object"]["discount_data"]["percentage"] = str(coupon.discount_value)

    response = requests.post(
        "https://connect.squareupsandbox.com/v2/catalog/object",
        headers={
            "Square-Version": "2025-11-15",
            "Authorization": f"Bearer {SQUARE_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json=body
    )

    result = response.json()

    try:
        return result["catalog_object"]["id"]
    except Exception:
        print("ERROR CREATING SQUARE DISCOUNT:", result)
        return None
