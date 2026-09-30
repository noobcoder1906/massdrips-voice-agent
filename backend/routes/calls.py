"""
backend/routes/calls.py

REST API endpoints for single call execution and transcript retrieval.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from backend.models import APIResponse
from backend.auth.api_key import get_current_tenant_from_key
from backend.services import get_lead, get_tenant, create_lead, create_call_log
from backend.telephony.factory import get_telephony_provider
from backend.database import get_db
from bson import ObjectId

router = APIRouter(prefix="/api/v1/calls", tags=["Calls"])


class SingleCallRequest(BaseModel):
    phone: str
    name: Optional[str] = "Lead"
    email: Optional[str] = None
    custom_context: Optional[str] = None


@router.post("/single", response_model=APIResponse)
async def trigger_single_call(
    req: SingleCallRequest,
    tenant: Dict[str, Any] = Depends(get_current_tenant_from_key)
):
    """
    Triggers an immediate outbound AI voice call to a single recipient.
    """
    tenant_id = tenant["id"]

    # 1. Create or fetch lead
    lead_data = {
        "tenant_id": tenant_id,
        "name": req.name,
        "phone": req.phone,
        "email": req.email,
        "notes": req.custom_context
    }
    lead_doc = await create_lead(lead_data)
    lead_id = lead_doc["id"]

    # 2. Get Telephony Provider
    provider_name = tenant.get("telephony_provider", "mock")
    provider = get_telephony_provider(provider_name)

    # 3. Dispatch call
    ws_url = f"ws://localhost:8000/ws/voice/{tenant_id}/{lead_id}"
    call_res = await provider.make_outbound_call(
        to_phone=req.phone,
        from_phone="+18005550199",
        websocket_url=ws_url,
        custom_data={"tenant_id": tenant_id, "lead_id": lead_id}
    )

    # 4. Log call initiation in DB (create_call_log returns call_log_id string)
    call_log_id = await create_call_log(tenant_id=tenant_id, lead_id=lead_id)

    return APIResponse(
        success=True,
        message="Outbound call initiated successfully",
        data={
            "call_sid": call_res.call_sid,
            "call_log_id": call_log_id,
            "status": call_res.status,
            "provider": provider_name,
            "recipient": req.phone
        }
    )


@router.get("", response_model=APIResponse)
async def list_calls(
    tenant_id: Optional[str] = Query(None),
    tenant: Dict[str, Any] = Depends(get_current_tenant_from_key)
):
    t_id = tenant_id or tenant["id"]
    db = get_db()
    cursor = db["calls"].find({"tenant_id": t_id}).sort("started_at", -1)
    docs = await cursor.to_list(length=100)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return APIResponse(success=True, message="Calls retrieved", data=docs)


@router.get("/{call_id}/transcript", response_model=APIResponse)
async def get_call_transcript(
    call_id: str,
    tenant: Dict[str, Any] = Depends(get_current_tenant_from_key)
):
    db = get_db()
    if not ObjectId.is_valid(call_id):
        raise HTTPException(status_code=400, detail="Invalid call_id format")

    doc = await db["calls"].find_one({"_id": ObjectId(call_id), "tenant_id": tenant["id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Call log not found")

    doc["id"] = str(doc.pop("_id"))
    return APIResponse(
        success=True,
        message="Transcript retrieved",
        data={
            "call_id": doc["id"],
            "started_at": doc.get("started_at"),
            "duration_sec": doc.get("duration_sec", 0),
            "transcript": doc.get("transcript", []),
            "outcome": doc.get("outcome"),
            "sentiment": doc.get("sentiment")
        }
    )
