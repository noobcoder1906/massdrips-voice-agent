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

from backend.agent.llm import get_llm_engine
from backend.agent.prompts import build_system_prompt
from backend.services.services import get_tenant_persona, get_lead_context, get_products_for_tenant


class ChatRequest(BaseModel):
    message: str
    tenant_id: Optional[str] = "mass-drips"
    lead_id: Optional[str] = "sample-lead-01"
    history: Optional[List[Dict[str, str]]] = []


@router.post("/chat")
async def live_chat_endpoint(req: ChatRequest):
    tenant_config = await get_tenant_persona(req.tenant_id)
    lead_info = await get_lead_context(req.lead_id, req.tenant_id)
    products = await get_products_for_tenant(req.tenant_id, in_stock_only=True, limit=10)

    system_prompt = build_system_prompt(
        tenant_config=tenant_config,
        lead_info=lead_info,
        products=products,
    )

    llm = get_llm_engine()
    tokens = []
    async for token in llm.stream_response(
        system_prompt=system_prompt,
        conversation_history=req.history,
        user_message=req.message,
    ):
        tokens.append(token)

    reply_text = "".join(tokens).strip()
    if not reply_text:
        reply_text = "Haan bilkul! Our 240 GSM hoodies and acid wash tees are in stock. Would you like me to send you the direct catalog link?"

    return {"success": True, "reply": reply_text}


class SpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = "my_voice"
    speed: Optional[float] = 1.0


@router.post("/speak")
async def live_speak_endpoint(req: SpeakRequest):
    """Synthesizes text using Kokoro neural ONNX engine and returns high-fidelity audio/wav bytes."""
    from fastapi.responses import Response
    from backend.voice.tts import KokoroTTS
    
    try:
        wav_bytes = KokoroTTS.synthesize_to_wav(req.text, voice=req.voice, speed=req.speed)
        return Response(content=wav_bytes, media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {e}")


@router.post("/upload-voice-clone")
async def upload_voice_clone(file: bytes = Body(...)):
    """Receives user audio sample and saves it for local voice cloning."""
    clones_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice", "clones")
    os.makedirs(clones_dir, exist_ok=True)
    out_path = os.path.join(clones_dir, "my_voice.wav")
    with open(out_path, "wb") as f:
        f.write(file)
    return {"success": True, "message": "Custom voice clone sample saved successfully!"}
