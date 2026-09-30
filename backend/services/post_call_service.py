"""
backend/services/post_call_service.py

Post-Call Action & Notification Generator.
Generates personalized SMS / WhatsApp follow-up payloads after voice call completion.
"""

from typing import Dict, Any, List, Optional


def generate_post_call_message(
    lead_name: str,
    brand_name: str,
    evaluation: Dict[str, Any],
    products_discussed: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Generates customized follow-up message text and action payload for lead.
    """
    outcome = evaluation.get("outcome", "interested")
    first_name = lead_name.split()[0] if lead_name else "there"

    discount_code = "DRIP10"
    base_url = "https://massdrips.com/catalog"

    if outcome == "converted":
        msg = f"Hi {first_name}! Thank you for your order with {brand_name}! 🎉 Your 10% discount code '{discount_code}' has been applied. Track your order here: {base_url}"
    elif outcome in ("interested", "callback"):
        prod_name = products_discussed[0]["name"] if products_discussed else "Drip Hoodie"
        msg = f"Hi {first_name}! Thanks for chatting with Aria at {brand_name}. Here is the link for {prod_name}: {base_url}. Use code '{discount_code}' for 10% OFF today!"
    else:
        msg = f"Hi {first_name}! Thanks for taking our call at {brand_name}. Explore our new streetwear collection anytime: {base_url}"

    return {
        "channel": "whatsapp",
        "recipient": lead_name,
        "message": msg,
        "discount_code": discount_code if outcome in ("converted", "interested", "callback") else None,
        "link": base_url
    }
