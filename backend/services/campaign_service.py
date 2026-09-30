"""
backend/services/campaign_service.py

Campaign DB Service for CRUD operations, lead management, and status updates.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from bson import ObjectId
from backend.database import get_db
from backend.models import CampaignCreate


def _to_id(doc: Dict[str, Any]) -> Dict[str, Any]:
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


async def create_campaign(data: CampaignCreate) -> Dict[str, Any]:
    db = get_db()
    now = datetime.now(timezone.utc)
    doc = data.model_dump()
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["total_leads"] = len(doc.get("lead_ids", []))
    doc["calls_made"] = 0
    doc["calls_answered"] = 0
    doc["conversions"] = 0
    # Track lead dispatch status per campaign
    doc["lead_states"] = {
        lead_id: {"status": "pending", "attempts": 0, "last_attempt": None}
        for lead_id in doc.get("lead_ids", [])
    }
    res = await db["campaigns"].insert_one(doc)
    created = await db["campaigns"].find_one({"_id": res.inserted_id})
    return _to_id(created)


async def get_campaign(campaign_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db = get_db()
    if not ObjectId.is_valid(campaign_id):
        return None
    query: Dict[str, Any] = {"_id": ObjectId(campaign_id)}
    if tenant_id:
        query["tenant_id"] = tenant_id
    doc = await db["campaigns"].find_one(query)
    return _to_id(doc) if doc else None


async def get_campaigns_for_tenant(tenant_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db["campaigns"].find({"tenant_id": tenant_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=100)
    return [_to_id(d) for d in docs]


async def update_campaign_status(campaign_id: str, status: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db = get_db()
    if not ObjectId.is_valid(campaign_id):
        return None
    query: Dict[str, Any] = {"_id": ObjectId(campaign_id)}
    if tenant_id:
        query["tenant_id"] = tenant_id
    await db["campaigns"].update_one(
        query,
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}}
    )
    return await get_campaign(campaign_id, tenant_id)


async def add_leads_to_campaign(campaign_id: str, lead_ids: List[str], tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    db = get_db()
    camp = await get_campaign(campaign_id, tenant_id)
    if not camp:
        return None

    existing_leads = set(camp.get("lead_ids", []))
    new_leads = [l for l in lead_ids if l not in existing_leads]
    if not new_leads:
        return camp

    updated_lead_ids = camp.get("lead_ids", []) + new_leads
    lead_states = camp.get("lead_states", {})
    for l_id in new_leads:
        lead_states[l_id] = {"status": "pending", "attempts": 0, "last_attempt": None}

    await db["campaigns"].update_one(
        {"_id": ObjectId(campaign_id)},
        {
            "$set": {
                "lead_ids": updated_lead_ids,
                "total_leads": len(updated_lead_ids),
                "lead_states": lead_states,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    return await get_campaign(campaign_id, tenant_id)


async def get_active_campaigns() -> List[Dict[str, Any]]:
    """Fetch all running campaigns for background worker."""
    db = get_db()
    cursor = db["campaigns"].find({"status": "running"})
    docs = await cursor.to_list(length=50)
    return [_to_id(d) for d in docs]


async def update_campaign_lead_state(
    campaign_id: str,
    lead_id: str,
    lead_status: str,
    increment_calls: bool = False,
    is_conversion: bool = False
) -> None:
    """Update lead call state in campaign and bump campaign counters."""
    db = get_db()
    if not ObjectId.is_valid(campaign_id):
        return

    camp = await db["campaigns"].find_one({"_id": ObjectId(campaign_id)})
    if not camp:
        return

    lead_states = camp.get("lead_states", {})
    current = lead_states.get(lead_id, {"status": "pending", "attempts": 0})
    current["status"] = lead_status
    current["attempts"] = current.get("attempts", 0) + 1
    current["last_attempt"] = datetime.now(timezone.utc).isoformat()
    lead_states[lead_id] = current

    update_fields: Dict[str, Any] = {"lead_states": lead_states, "updated_at": datetime.now(timezone.utc)}
    inc_fields: Dict[str, int] = {}
    if increment_calls:
        inc_fields["calls_made"] = 1
    if lead_status in ("completed", "answered"):
        inc_fields["calls_answered"] = 1
    if is_conversion:
        inc_fields["conversions"] = 1

    update_doc: Dict[str, Any] = {"$set": update_fields}
    if inc_fields:
        update_doc["$inc"] = inc_fields

    await db["campaigns"].update_one({"_id": ObjectId(campaign_id)}, update_doc)
