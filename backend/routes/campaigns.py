"""
backend/routes/campaigns.py

REST API endpoints for Campaign CRUD operations, execution control, and CSV uploads.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
import csv
import io
from backend.models import CampaignCreate, CampaignResponse, APIResponse, LeadCreate
from backend.services import (
    create_campaign,
    get_campaign,
    get_campaigns_for_tenant,
    update_campaign_status,
    add_leads_to_campaign,
    create_lead
)

router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns"])


@router.post("", response_model=APIResponse)
async def create_new_campaign(campaign: CampaignCreate):
    res = await create_campaign(campaign)
    return APIResponse(success=True, message="Campaign created successfully", data=res)


@router.get("", response_model=APIResponse)
async def list_campaigns(tenant_id: str = Query(..., description="Tenant ID")):
    res = await get_campaigns_for_tenant(tenant_id)
    return APIResponse(success=True, message="Campaigns retrieved", data=res)


@router.get("/{campaign_id}", response_model=APIResponse)
async def get_campaign_detail(campaign_id: str, tenant_id: Optional[str] = None):
    res = await get_campaign(campaign_id, tenant_id)
    if not res:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return APIResponse(success=True, message="Campaign detail retrieved", data=res)


@router.post("/{campaign_id}/start", response_model=APIResponse)
async def start_campaign(campaign_id: str, tenant_id: Optional[str] = None):
    res = await update_campaign_status(campaign_id, "running", tenant_id)
    if not res:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return APIResponse(success=True, message="Campaign started", data=res)


@router.post("/{campaign_id}/pause", response_model=APIResponse)
async def pause_campaign(campaign_id: str, tenant_id: Optional[str] = None):
    res = await update_campaign_status(campaign_id, "paused", tenant_id)
    if not res:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return APIResponse(success=True, message="Campaign paused", data=res)


@router.post("/{campaign_id}/leads/csv", response_model=APIResponse)
async def upload_campaign_leads_csv(
    campaign_id: str,
    tenant_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Parse CSV file containing leads (name, phone, email, etc.), save leads to DB,
    and attach them to the specified campaign.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    created_lead_ids = []
    for row in reader:
        name = row.get("name") or row.get("Name", "Unknown Lead")
        phone = row.get("phone") or row.get("Phone", "")
        email = row.get("email") or row.get("Email", None)

        if not phone:
            continue

        lead_data = LeadCreate(
            tenant_id=tenant_id,
            name=name,
            phone=phone,
            email=email,
            status="new"
        )
        lead_doc = await create_lead(lead_data)
        created_lead_ids.append(lead_doc["id"])

    updated_camp = await add_leads_to_campaign(campaign_id, created_lead_ids, tenant_id)
    if not updated_camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return APIResponse(
        success=True,
        message=f"Imported {len(created_lead_ids)} leads into campaign",
        data={"campaign_id": campaign_id, "imported_count": len(created_lead_ids)}
    )
