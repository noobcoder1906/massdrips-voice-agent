"""
backend/services/tenant_service.py
backend/services/lead_service.py
backend/services/product_service.py

Combined service layer for MongoDB queries.
Used by the WebSocket handler (live session context)
and REST API routes (CRUD operations).
"""

from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from backend.database import get_db


# ── Helper ─────────────────────────────────────────────────────────────────────
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _doc_to_dict(doc: dict) -> dict:
    """Convert MongoDB document: ObjectId → str, _id → id."""
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


# ══════════════════════════════════════════════════════════════════════════════
# TENANT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

async def create_tenant(data: dict) -> dict:
    db = get_db()
    data["created_at"] = _now()
    data["updated_at"] = _now()
    result = await db["tenants"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data


async def get_tenant(tenant_id: str) -> Optional[dict]:
    db = get_db()
    try:
        doc = await db["tenants"].find_one({"_id": ObjectId(tenant_id)})
    except Exception:
        doc = await db["tenants"].find_one({"slug": tenant_id})
    return _doc_to_dict(doc) if doc else None


async def get_all_tenants() -> list[dict]:
    db = get_db()
    cursor = db["tenants"].find({}).sort("created_at", -1)
    return [_doc_to_dict(d) async for d in cursor]


async def update_tenant(tenant_id: str, data: dict) -> Optional[dict]:
    db = get_db()
    data["updated_at"] = _now()
    await db["tenants"].update_one(
        {"_id": ObjectId(tenant_id)},
        {"$set": data}
    )
    return await get_tenant(tenant_id)


async def get_tenant_persona(tenant_id: str) -> dict:
    """
    Returns the persona config dict for a tenant.
    Falls back to defaults if tenant not found.
    """
    tenant = await get_tenant(tenant_id)
    if not tenant:
        return {
            "name":       "Aria",
            "brand":      "VoxSales",
            "language":   "english",
            "tone":       "friendly",
            "agent_type": "sales",
            "max_response_words": 60,
        }
    persona = tenant.get("persona", {})
    return {
        "name":               persona.get("agent_name", "Aria"),
        "brand":              persona.get("brand_name", tenant.get("name", "VoxSales")),
        "language":           persona.get("language", "english"),
        "tone":               persona.get("tone", "friendly"),
        "agent_type":         persona.get("agent_type", "sales"),
        "max_response_words": persona.get("max_words", 60),
    }


# ══════════════════════════════════════════════════════════════════════════════
# LEAD SERVICE
# ══════════════════════════════════════════════════════════════════════════════

async def create_lead(data: dict) -> dict:
    db = get_db()
    data["created_at"]   = _now()
    data["updated_at"]   = _now()
    data["call_count"]   = 0
    data["lead_score"]   = 0
    data["status"]       = data.get("status", "new")
    result = await db["leads"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data


async def get_lead(lead_id: str, tenant_id: Optional[str] = None) -> Optional[dict]:
    db = get_db()
    query = {"_id": ObjectId(lead_id)}
    if tenant_id:
        query["tenant_id"] = tenant_id
    try:
        doc = await db["leads"].find_one(query)
    except Exception:
        return None
    return _doc_to_dict(doc) if doc else None


async def get_leads_for_tenant(tenant_id: str, limit: int = 50) -> list[dict]:
    db = get_db()
    cursor = db["leads"].find({"tenant_id": tenant_id}).sort("created_at", -1).limit(limit)
    return [_doc_to_dict(d) async for d in cursor]


async def update_lead_after_call(
    lead_id: str,
    summary: str,
    outcome: Optional[str] = None,
    score_delta: int = 0,
) -> None:
    """Update lead after a call completes — summary, status, score."""
    db = get_db()
    update = {
        "last_interaction_summary": summary,
        "last_call_at":             _now(),
        "updated_at":               _now(),
        "$inc": {"call_count": 1, "lead_score": score_delta},
    }
    if outcome:
        update["status"] = outcome
    await db["leads"].update_one(
        {"_id": ObjectId(lead_id)},
        {"$set": {k: v for k, v in update.items() if k != "$inc"},
         "$inc": {"call_count": 1, "lead_score": score_delta}}
    )


async def get_lead_context(lead_id: str, tenant_id: Optional[str] = None) -> dict:
    """
    Returns lead info dict shaped for prompt injection.
    Safe fallback if lead not found.
    """
    lead = await get_lead(lead_id, tenant_id)
    if not lead:
        return {
            "id":                        lead_id,
            "name":                      "Customer",
            "interests":                 [],
            "last_interaction_summary":  "",
        }
    return {
        "id":                       lead.get("id", lead_id),
        "name":                     lead.get("name", "Customer"),
        "interests":                lead.get("interests", []),
        "last_interaction_summary": lead.get("last_interaction_summary", ""),
        "tags":                     lead.get("tags", []),
        "language":                 lead.get("language", "english"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT SERVICE
# ══════════════════════════════════════════════════════════════════════════════

async def create_product(data: dict) -> dict:
    db = get_db()
    data["created_at"] = _now()
    data["updated_at"] = _now()
    result = await db["products"].insert_one(data)
    data["id"] = str(result.inserted_id)
    return data


async def get_products_for_tenant(
    tenant_id: str,
    in_stock_only: bool = True,
    limit: int = 20,
) -> list[dict]:
    db = get_db()
    query = {"tenant_id": tenant_id}
    if in_stock_only:
        query["in_stock"] = True
    cursor = db["products"].find(query).sort("name", 1).limit(limit)
    return [_doc_to_dict(d) async for d in cursor]


async def search_products(tenant_id: str, query_str: str) -> list[dict]:
    """Simple text search on product name + description."""
    db = get_db()
    regex = {"$regex": query_str, "$options": "i"}
    cursor = db["products"].find({
        "tenant_id": tenant_id,
        "$or": [{"name": regex}, {"description": regex}, {"tags": regex}]
    }).limit(10)
    return [_doc_to_dict(d) async for d in cursor]


# ══════════════════════════════════════════════════════════════════════════════
# CALL LOG SERVICE
# ══════════════════════════════════════════════════════════════════════════════

async def create_call_log(tenant_id: str, lead_id: str, **kwargs) -> str:
    db = get_db()
    doc = {
        "tenant_id":  tenant_id,
        "lead_id":    lead_id,
        "status":     "active",
        "direction":  "inbound",
        "transcript": [],
        "started_at": _now(),
        "created_at": _now(),
        **kwargs,
    }
    result = await db["calls"].insert_one(doc)
    return str(result.inserted_id)


async def append_transcript(call_id: str, role: str, text: str) -> None:
    db = get_db()
    await db["calls"].update_one(
        {"_id": ObjectId(call_id)},
        {"$push": {"transcript": {"role": role, "text": text, "ts": _now()}}}
    )


async def close_call_log(
    call_id: str,
    duration_sec: int,
    outcome: Optional[str] = None,
    sentiment: Optional[str] = None,
) -> None:
    db = get_db()
    await db["calls"].update_one(
        {"_id": ObjectId(call_id)},
        {"$set": {
            "status":       "completed",
            "ended_at":     _now(),
            "duration_sec": duration_sec,
            "outcome":      outcome,
            "sentiment":    sentiment,
        }}
    )
