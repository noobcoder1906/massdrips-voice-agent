"""
backend/agent/entity_resolver.py

Dynamic Entity Resolution for Mass Drips Voice Agent.
Maps any actor/character/film/dialogue the user says to the closest catalog product.
"""

from __future__ import annotations
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

PRODUCT_CATALOG = [
    {
        "id": "MD001",
        "name": "Jana Nayagan — Crowd Edition",
        "price": 699, "category": "Kollywood", "gsm": "240 GSM Heavyweight Tee", "badge": "HOT",
        "aliases": [
            "jana nayagan", "nayagan", "jana", "rajinikanth", "rajini", "superstar",
            "thalaivar", "thalaiva", "kabali", "kaala", "darbar", "jailer", "annaatthe",
            "robot", "enthiran", "muthu", "baasha", "padayappa", "sivaji", "vettaiyaadu",
        ],
    },
    {
        "id": "MD008",
        "name": "Jana Nayagan — The People's Hero",
        "price": 799, "category": "Kollywood", "gsm": "240 GSM Dark Silhouette Tee", "badge": "LIMITED",
        "aliases": ["peoples hero", "silhouette rajini", "dark rajini", "limited rajini"],
    },
    {
        "id": "MD010",
        "name": "Thalapathy Forever Statement Tee",
        "price": 799, "category": "Kollywood", "gsm": "240 GSM Statement Tee", "badge": "BESTSELLER",
        "aliases": [
            "thalapathy", "vijay", "thalapathy vijay", "leo", "beast", "master",
            "bigil", "mersal", "theri", "ghilli", "sarkar", "varisu", "goat",
            "ilayathalapathy", "joseph vijay", "thalapathy vijay",
        ],
    },
    {
        "id": "MD027",
        "name": "AK — The Don's Edition",
        "price": 1499, "category": "Kollywood", "gsm": "380 GSM Fleece Drop Hoodie", "badge": "LIMITED",
        "aliases": [
            "ajith", "ajit", "ajith kumar", "ajit kumar", "ajithkumar",
            "thala", "thala ajith", "ak", "don", "mankatha", "thunivu",
            "vedalam", "vivegam", "yennai arindhaal", "arrambam", "billa",
            "valimai", "villian", "good bad ugly", "nerkonda paarvai", "junga",
        ],
    },
    {
        "id": "MD009",
        "name": "Flower Nahi, FIRE (Pushpa)",
        "price": 699, "category": "Tollywood", "gsm": "240 GSM Wildfire Tee", "badge": "HOT",
        "aliases": [
            "pushpa", "pushpa raj", "allu arjun", "allu", "flower nahi fire",
            "flower nahi", "fire tee", "pushpa the rise", "pushpa 2", "icon star",
            "bunny", "srivalli",
        ],
    },
    {
        "id": "MD_JNS",
        "name": "Jhukega Nahi Saala",
        "price": 699, "category": "Tollywood", "gsm": "240 GSM Tee", "badge": "TRENDING",
        "aliases": [
            "jhukega nahi saala", "jhukhega nahi saala", "jukhega nahi sala",
            "jukka nahi sala", "jhukega", "jukhega", "jhukhega", "jhukke",
            "jhuka nahi", "saala", "nahi jhukenge", "pushpa defiance",
        ],
    },
    {
        "id": "MD003",
        "name": "Main Rukta Nahi Hoon (Sweatshirt)",
        "price": 1199, "category": "Bollywood", "gsm": "240 GSM Sweatshirt", "badge": "NEW",
        "aliases": ["main rukta nahi sweatshirt", "rukta nahi sweatshirt", "srk sweatshirt"],
    },
    {
        "id": "MD004",
        "name": "Main Rukta Nahi Hoon (Tee)",
        "price": 699, "category": "Bollywood", "gsm": "240 GSM Oversized Tee", "badge": "TRENDING",
        "aliases": [
            "main rukta nahi hoon", "main rukta nahi", "rukta nahi", "main rukta",
            "srk tee", "shahrukh tee", "shah rukh khan", "srk", "king khan",
            "pathaan", "jawan", "dilwale", "don srk", "shahrukh",
        ],
    },
    {
        "id": "MD005",
        "name": "Kismat Der Se Aye (Cracked Tee)",
        "price": 699, "category": "Bollywood", "gsm": "240 GSM Cracked Wall Tee", "badge": "TRENDING",
        "aliases": ["kismat", "kismat der se aye", "kismat der se", "fate tee", "cracked tee"],
    },
    {
        "id": "MD006",
        "name": "Kismat Der Se Aye (Melange Grey Hoodie)",
        "price": 1599, "category": "Heavyweights", "gsm": "240 GSM Cracked Hoodie", "badge": "NEW",
        "aliases": ["kismat grey hoodie", "kismat melange", "grey kismat", "melange hoodie"],
    },
    {
        "id": "MD007",
        "name": "Kismat Der Se Aye (White Hoodie)",
        "price": 1599, "category": "Heavyweights", "gsm": "240 GSM Cracked Hoodie", "badge": "HOT",
        "aliases": ["kismat white hoodie", "white kismat", "cracked white hoodie"],
    },
    {
        "id": "MD002",
        "name": "In The Shadows We Forge",
        "price": 1499, "category": "Heavyweights", "gsm": "240 GSM Oversized Hoodie", "badge": "BESTSELLER",
        "aliases": [
            "shadows", "in the shadows", "shadows we forge", "forge",
            "dark hoodie", "cyberpunk hoodie", "heavy hoodie", "bestseller hoodie",
        ],
    },
    {
        "id": "MD_LOVE",
        "name": "Some Feelings Don't Need Words",
        "price": 799, "category": "Love Edition", "gsm": "240 GSM Aesthetic Tee", "badge": "NEW",
        "aliases": [
            "feelings", "love tee", "love edition", "some feelings",
            "don't need words", "romantic tee", "aesthetic",
        ],
    },
]

COLLECTION_ALIASES = {
    "kollywood": "Kollywood",
    "tamil cinema": "Kollywood",
    "tamil movies": "Kollywood",
    "south indian": "Kollywood",
    "tollywood": "Tollywood",
    "telugu": "Tollywood",
    "telugu cinema": "Tollywood",
    "bollywood": "Bollywood",
    "hindi cinema": "Bollywood",
    "hindi movies": "Bollywood",
    "heavyweights": "Heavyweights",
    "hoodies": "Heavyweights",
    "love edition": "Love Edition",
    "romance": "Love Edition",
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _token_overlap(q_tokens: set, a_tokens: set) -> float:
    if not a_tokens or not q_tokens:
        return 0.0
    return len(q_tokens & a_tokens) / min(len(q_tokens), len(a_tokens))


def _substring_score(query: str, alias: str) -> float:
    if alias in query:
        return min(1.0, len(alias.split()) / max(1, len(query.split())) * 2)
    if len(alias) >= 4 and len(query) >= 4:
        # partial token match: check each alias token in query
        alias_tokens = alias.split()
        hits = sum(1 for t in alias_tokens if t in query and len(t) >= 3)
        if hits:
            return hits / len(alias_tokens) * 0.8
    return 0.0


def resolve(user_text: str, top_k: int = 2) -> list[dict]:
    """Resolve user speech to matching catalog products. Returns top_k matches."""
    query = _normalize(user_text)
    query_tokens = set(query.split())
    scored = []

    for product in PRODUCT_CATALOG:
        best_score = 0.0
        best_alias = ""
        for alias in product["aliases"]:
            norm_alias = _normalize(alias)
            alias_tokens = set(norm_alias.split())
            score = max(
                _substring_score(query, norm_alias),
                _token_overlap(query_tokens, alias_tokens),
            )
            if score > best_score:
                best_score = score
                best_alias = alias

        if best_score >= 0.25:
            scored.append({**product, "match_score": round(best_score, 3), "matched_alias": best_alias})

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_k]


def resolve_collection(user_text: str) -> Optional[str]:
    query = _normalize(user_text)
    for alias, collection in COLLECTION_ALIASES.items():
        if alias in query:
            return collection
    return None


def build_product_context(user_text: str) -> Optional[str]:
    """
    Main API: resolve user text -> LLM context injection string.
    Returns a string to inject into the system prompt, or None.
    """
    matches = resolve(user_text, top_k=2)
    collection = resolve_collection(user_text)
    parts = []

    if matches:
        top = matches[0]
        score = top["match_score"]
        name = top["name"]
        price = top["price"]
        badge = top["badge"]
        gsm = top["gsm"]
        cat = top["category"]

        if score >= 0.6:
            parts.append(
                f"ENTITY RESOLVED (confident): User is asking about '{name}' "
                f"(Rs {price}, {gsm}, {badge} from {cat} collection). "
                f"This product EXISTS. Confirm it and share price."
            )
        elif score >= 0.3:
            parts.append(
                f"ENTITY RESOLVED (fuzzy): User likely means '{name}' "
                f"(Rs {price}, {cat}, {badge}). "
                f"Confirm by referencing the product name naturally, then give price and offer WhatsApp."
            )
            if len(matches) > 1:
                alt = matches[1]
                parts.append(
                    f"Alternative if wrong: '{alt['name']}' at Rs {alt['price']}."
                )

    elif collection:
        coll_products = [p for p in PRODUCT_CATALOG if p["category"] == collection][:3]
        if coll_products:
            names = ", ".join(f"{p['name']} at Rs {p['price']}" for p in coll_products)
            parts.append(
                f"COLLECTION MATCH: User wants {collection} designs. "
                f"Top picks: {names}. Ask which star/film they like most."
            )

    return " | ".join(parts) if parts else None


if __name__ == "__main__":
    tests = [
        "Do you have Ajith Kumar collections?",
        "I want the Vijay tee",
        "Jukka nahi sala wala chahiye",
        "Pushpa design dena",
        "Got anything for Rajinikanth?",
        "Main Rukta Nahi Hoon sweatshirt",
        "Do you have any Tollywood designs?",
        "Black hoodie chahiye",
        "What about SRK?",
        "Thalapathy ka design hai?",
        "Kismat der se aye hoodie",
        "Jana Nayagan tee",
    ]
    print("=" * 60)
    for q in tests:
        ctx = build_product_context(q)
        print(f"Q: {q}\n → {ctx or 'No match'}\n")
