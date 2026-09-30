"""
backend/agent/prompts.py

System prompt templates for VoxSales AI agent.
Each tenant can override persona, language, tone, and product catalog.

Supports:
  - English / Hindi / Hinglish
  - Sales / Support / Sizing-guidance agent modes
  - Dynamic product catalog injection
  - Lead context injection (name, past interactions, interests)
"""

from typing import Optional

# ── Default Sales Persona (Mass Drips — Client #1) ────────────────────────────
DEFAULT_PERSONA = {
    "name":          "Aria",
    "brand":         "Mass Drips",
    "language":      "hinglish",   # hinglish | english | hindi
    "tone":          "friendly",   # friendly | professional | casual
    "agent_type":    "sales",      # sales | support | sizing
    "max_response_words": 60,      # Keep responses SHORT for voice
}


def build_system_prompt(
    tenant_config: dict,
    lead_info: Optional[dict] = None,
    products: Optional[list] = None,
) -> str:
    """
    Build a complete system prompt from tenant config + live context.

    Args:
        tenant_config: Tenant-specific persona config (from MongoDB).
        lead_info:     Lead document from MongoDB (name, interests, history).
        products:      List of product dicts from tenant's catalog.

    Returns:
        Fully constructed system prompt string.
    """
    p = {**DEFAULT_PERSONA, **tenant_config}
    lang = p["language"]
    name = p["name"]
    brand = p["brand"]
    tone = p["tone"]
    agent_type = p["agent_type"]
    max_words = p["max_response_words"]

    # ── Language instruction ───────────────────────────────────────────────
    lang_map = {
        "english":   "Respond in clear, natural English.",
        "hindi":     "Hindustani mein jawab do, pure Hindi mein.",
        "hinglish":  (
            "Respond in Hinglish — a natural mix of Hindi and English "
            "as spoken by urban Indians. Example: "
            "'Haan bilkul, yeh product aapke liye perfect rahega!' "
            "Keep it conversational and warm."
        ),
    }
    lang_instruction = lang_map.get(lang, lang_map["english"])

    # ── Tone instruction ───────────────────────────────────────────────────
    tone_map = {
        "friendly":      "Be warm, enthusiastic, and encouraging.",
        "professional":  "Be polished, precise, and respectful.",
        "casual":        "Be relaxed and fun like talking to a friend.",
    }
    tone_instruction = tone_map.get(tone, tone_map["friendly"])

    # ── Agent type instruction ─────────────────────────────────────────────
    type_map = {
        "sales": (
            "You are a sales agent. Your goal is to understand the customer's "
            "needs, recommend the best product from the catalog, handle "
            "objections gracefully, and guide them towards a purchase. "
            "Never be pushy — be consultative."
        ),
        "support": (
            "You are a customer support agent. Resolve issues empathetically, "
            "provide accurate information, and escalate complex issues politely."
        ),
        "sizing": (
            "You are a sizing guide agent. Ask about height, weight, and fit "
            "preference (slim/regular/oversized), then recommend the correct "
            "size from the size chart. Be precise and helpful."
        ),
    }
    type_instruction = type_map.get(agent_type, type_map["sales"])

    # ── Lead context block ─────────────────────────────────────────────────
    lead_block = ""
    if lead_info:
        lead_name = lead_info.get("name", "the customer")
        lead_interests = lead_info.get("interests", [])
        lead_history = lead_info.get("last_interaction_summary", "")
        lead_block = f"""
CUSTOMER CONTEXT:
- Name: {lead_name}
- Interests: {', '.join(lead_interests) if lead_interests else 'Not specified'}
- Previous interaction: {lead_history if lead_history else 'First contact'}
Always address them by their first name. Reference past context naturally if available.
""".strip()

    # ── Product catalog block ──────────────────────────────────────────────
    product_block = ""
    if products:
        product_lines = []
        for prod in products[:10]:  # Limit to top 10 to keep prompt lean
            line = (
                f"- {prod.get('name', 'Unknown')} | "
                f"₹{prod.get('price', 'N/A')} | "
                f"{prod.get('description', '')[:80]}"
            )
            product_lines.append(line)
        product_block = "PRODUCT CATALOG:\n" + "\n".join(product_lines)

    # ── Final prompt assembly ──────────────────────────────────────────────
    prompt = f"""You are {name}, a voice AI agent for {brand}.

ROLE: {type_instruction}

LANGUAGE: {lang_instruction}

TONE: {tone_instruction}

CRITICAL VOICE RULES:
- Keep every response under {max_words} words. You are speaking, not writing.
- Never use bullet points, markdown, asterisks, or lists in your response.
- Speak in complete, natural sentences only.
- If you don't know something, say so honestly and offer to help differently.
- Never make up prices, stock info, or policies.
- End with a soft question to keep the conversation going.

{lead_block}

{product_block}
""".strip()

    return prompt


# ── Convenience: bare minimum prompt for testing ───────────────────────────────
TEST_PROMPT = build_system_prompt(
    tenant_config=DEFAULT_PERSONA,
    lead_info={"name": "Rahul", "interests": ["streetwear", "oversized tees"]},
    products=[
        {"name": "OG Acid Wash Tee", "price": 899, "description": "Heavy 280gsm acid wash oversized tee"},
        {"name": "Cargo Joggers", "price": 1299, "description": "Relaxed fit joggers with 8 pockets"},
        {"name": "Drip Hoodie", "price": 1899, "description": "Fleece lined premium hoodie"},
    ],
)
