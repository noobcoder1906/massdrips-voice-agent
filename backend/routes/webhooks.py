"""
backend/routes/webhooks.py

REST API endpoints for managing Webhook URLs and CRM event subscriptions.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from backend.models import APIResponse
from backend.auth.api_key import get_current_tenant_from_key
from backend.services import update_tenant
from backend.database import get_db

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


class WebhookConfig(BaseModel):
    webhook_url: str
    events: List[str] = ["call.completed", "lead.converted"]
    is_active: bool = True


@router.post("", response_model=APIResponse)
async def register_webhook(
    config: WebhookConfig,
    tenant: Dict[str, Any] = Depends(get_current_tenant_from_key)
):
    """
    Registers or updates the CRM webhook URL for the authenticated tenant.
    """
    tenant_id = tenant["id"]
    updated = await update_tenant(
        tenant_id,
        {
            "webhook_url": config.webhook_url,
            "webhook_events": config.events,
            "webhook_active": config.is_active
        }
    )
    return APIResponse(
        success=True,
        message="Webhook URL registered successfully",
        data={
            "tenant_id": tenant_id,
            "webhook_url": config.webhook_url,
            "events": config.events,
            "is_active": config.is_active
        }
    )


@router.get("", response_model=APIResponse)
async def get_webhook_config(
    tenant: Dict[str, Any] = Depends(get_current_tenant_from_key)
):
    """
    Fetches the current webhook configuration for the tenant.
    """
    return APIResponse(
        success=True,
        message="Webhook configuration retrieved",
        data={
            "tenant_id": tenant["id"],
            "webhook_url": tenant.get("webhook_url"),
            "webhook_events": tenant.get("webhook_events", ["call.completed"]),
            "webhook_active": tenant.get("webhook_active", False)
        }
    )

from fastapi import Request
from fastapi.responses import Response
import os

@router.post("/twilio/incoming")
async def twilio_incoming(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    
    tenant_id = "6abd262975108fde8f7b524c"
    lead_id = "twilio_" + call_sid
    
    server_host = os.getenv("SERVER_HOST", "164.52.212.94:8000")
    ws_url = f"ws://{server_host}/ws/voice/{tenant_id}/{lead_id}"
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_url}" />
    </Connect>
</Response>'''
    return Response(content=twiml, media_type="text/xml")
