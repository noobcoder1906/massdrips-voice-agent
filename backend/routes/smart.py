"""
backend/routes/smart.py

REST API endpoints for Premium Smart Features:
  - AI Lead Scoring
  - Post-call WhatsApp/SMS message generation
  - CRM Webhook test dispatch
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.agent.lead_scorer import evaluate_call_transcript
from backend.services.post_call_service import generate_post_call_message
from backend.services.webhook_service import dispatch_call_webhook
from backend.models import APIResponse

router = APIRouter(prefix="/api/v1/smart", tags=["Smart Features"])


class ScoreRequest(BaseModel):
    transcript: List[Dict[str, Any]]
    lead_name: Optional[str] = "Customer"
    brand_name: Optional[str] = "Mass Drips"


class WebhookTestRequest(BaseModel):
    webhook_url: str
    call_id: str
    tenant_id: str
    lead_id: str
    score: int
    sentiment: str
    outcome: str
    summary: str


@router.post("/score-transcript", response_model=APIResponse)
async def score_transcript(req: ScoreRequest):
    evaluation = evaluate_call_transcript(req.transcript)
    post_call_msg = generate_post_call_message(req.lead_name, req.brand_name, evaluation)
    return APIResponse(
        success=True,
        message="Transcript evaluated successfully",
        data={
            "evaluation": evaluation,
            "post_call_action": post_call_msg
        }
    )


@router.post("/dispatch-webhook", response_model=APIResponse)
async def test_webhook_dispatch(req: WebhookTestRequest):
    payload = {
        "event": "call.completed",
        "call_id": req.call_id,
        "tenant_id": req.tenant_id,
        "lead_id": req.lead_id,
        "ai_analysis": {
            "score": req.score,
            "sentiment": req.sentiment,
            "outcome": req.outcome,
            "summary": req.summary
        }
    }
    sent = await dispatch_call_webhook(req.webhook_url, payload)
    return APIResponse(
        success=sent,
        message="Webhook dispatched successfully" if sent else "Webhook dispatch failed",
        data={"webhook_url": req.webhook_url, "delivered": sent}
    )
