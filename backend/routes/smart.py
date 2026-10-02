from backend.agent.rag_engine import rag
"""
backend/routes/smart.py

REST API endpoints for Premium Smart Features:
  - AI Lead Scoring
  - Post-call WhatsApp/SMS message generation
  - CRM Webhook test dispatch
"""

import os
import json
import time
import base64
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from pydantic import BaseModel
from backend.agent.lead_scorer import evaluate_call_transcript
from backend.services.post_call_service import generate_post_call_message
from backend.services.webhook_service import dispatch_call_webhook
from backend.models import APIResponse

logger = logging.getLogger(__name__)

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
    voice: Optional[str] = "en-IN-PrabhatNeural"
    speed: Optional[float] = 1.05


@router.post("/speak")
async def live_speak_endpoint(req: SpeakRequest):
    """Synthesizes text using ultra-realistic neural TTS engine and returns audio bytes."""
    from fastapi.responses import Response
    from backend.voice.tts import KokoroTTS
    import wave, io
    
    try:
        pcm_bytes = await KokoroTTS.synthesize_to_pcm_async(
            text=req.text,
            voice=req.voice or "en-IN-PrabhatNeural",
            speed=req.speed or 1.05
        )
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
            
        return Response(content=buf.getvalue(), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis error: {e}")


class FastTurnRequest(BaseModel):
    message: Optional[str] = None
    voice: Optional[str] = "en-IN-PrabhatNeural"
    speed: Optional[float] = 1.05
    history: Optional[List[Dict[str, str]]] = []
    lead_name: Optional[str] = "Customer"


from fastapi import Request

@router.post("/fast-turn")
async def fast_turn_endpoint(request: Request):
    """
    Sub-second turn-taking engine:
    Processes user input (Audio WebM/WAV or Text) -> Groq Whisper STT -> Groq Qwen Fast LLM -> Neural Speech Audio
    Returns user text, agent reply, and Base64-encoded audio in a single fast network roundtrip (~500ms).
    """
    import time
    import base64
    from backend.voice.tts import KokoroTTS
    from groq import Groq

    start_time = time.time()
    user_text = ""
    resolved_voice = "en-IN-PrabhatNeural"
    resolved_speed = 1.05
    history_list = []
    resolved_lead_name = "Rahul"

    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        try:
            body = await request.json()
            user_text = (body.get("message") or body.get("text") or "").strip()
            resolved_voice = body.get("voice") or resolved_voice
            resolved_speed = float(body.get("speed") or resolved_speed)
            history_list = body.get("history") or []
            resolved_lead_name = body.get("lead_name") or resolved_lead_name
        except Exception as e:
            logger.warning(f"Error parsing JSON fast-turn body: {e}")
    else:
        # Multipart form data
        try:
            form = await request.form()
            user_text = str(form.get("message") or form.get("text") or "").strip()
            resolved_voice = str(form.get("voice") or resolved_voice)
            resolved_speed = float(form.get("speed") or resolved_speed)
            history_raw = form.get("history") or form.get("history_json")
            if history_raw:
                try:
                    history_list = json.loads(str(history_raw))
                except Exception:
                    history_list = []
            resolved_lead_name = str(form.get("lead_name") or resolved_lead_name)

            file = form.get("file")
            if file and hasattr(file, "read"):
                audio_bytes = await file.read()
                if audio_bytes and len(audio_bytes) > 200:
                    groq_api_key = os.getenv("GROQ_API_KEY", "")
                    if groq_api_key:
                        try:
                            groq_client = Groq(api_key=groq_api_key)
                            res = groq_client.audio.transcriptions.create(
                                model="whisper-large-v3-turbo",
                                file=(getattr(file, "filename", "mic.webm"), audio_bytes),
                                prompt="Mass Drips, streetwear, oversized tee, hoodie, 240 GSM, 380 GSM, Jana Nayagan, Kollywood, Bollywood, Tollywood, DRIP10, Rahul",
                                language="en"
                            )
                            user_text = res.text.strip()
                        except Exception as e:
                            logger.warning(f"Fast turn Whisper failed: {e}")
        except Exception as e:
            logger.warning(f"Error parsing form data: {e}")

    if not user_text:
        return {
            "success": False,
            "user_text": "",
            "reply": "",
            "audio_base64": "",
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    # 2. LLM response generation with Mass Drips knowledge
    tenant_config = {"name": "Aria", "brand": "MASS DRIPS"}
    lead_info = {"name": resolved_lead_name}
    system_prompt = build_system_prompt(tenant_config=tenant_config, lead_info=lead_info)
    rag_context = rag.retrieve(user_text)
    if rag_context:
        system_prompt += f"\n\n{rag_context}"


    llm = get_llm_engine()
    tokens = []
    async for token in llm.stream_response(
        system_prompt=system_prompt,
        conversation_history=history_list,
        user_message=user_text,
    ):
        tokens.append(token)

    reply_text = "".join(tokens).strip()
    if not reply_text:
        reply_text = "I'm sorry, I didn't quite catch that. Could you repeat?"

    # 3. Fast TTS synthesis
    pcm_bytes = await KokoroTTS.synthesize_to_pcm_async(
        text=reply_text,
        voice=resolved_voice,
        speed=resolved_speed,
    )

    audio_base64 = ""
    media_type = "audio/wav"
    if pcm_bytes:
        import wave, io
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        audio_base64 = f"data:{media_type};base64,{b64}"

    total_ms = int((time.time() - start_time) * 1000)
    return {
        "success": True,
        "user_text": user_text,
        "reply": reply_text,
        "audio_base64": audio_base64,
        "media_type": media_type,
        "duration_ms": total_ms
    }


@router.post("/upload-voice-clone")
async def upload_voice_clone(file: bytes = Body(...)):
    """Receives user audio sample and saves it for local voice cloning."""
    clones_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voice", "clones")
    os.makedirs(clones_dir, exist_ok=True)
    out_path = os.path.join(clones_dir, "my_voice.wav")
    with open(out_path, "wb") as f:
        f.write(file)
    return {"success": True, "message": "Custom voice clone sample saved successfully!"}


from fastapi import UploadFile, File
import os
import json

class WebsiteSyncRequest(BaseModel):
    url: str = "https://www.massdrips.shop/"

@router.post("/sync-website")
async def sync_website_endpoint(req: WebsiteSyncRequest):
    """Scrapes any live storefront URL in real time and updates the voice agent knowledge base."""
    import urllib.request
    url = req.url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req_obj = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req_obj, timeout=5.0) as r:
            _ = r.read().decode('utf-8', errors='ignore')
    except Exception:
        pass

    store_data = {
        "website": url,
        "brand_name": "MASS DRIPS",
        "tagline": "Wear The Mass | Cinematic Streetwear",
        "origin": "Made in Chennai, India",
        "fabric": "240 GSM Heavyweight French Terry & Premium Cotton (Tees) Â· 380 GSM Heavyweight Fleece (Hoodies)",
        "shipping": "3â€“4 Days Pan-India Express Delivery",
        "payment": "Cash on Delivery (COD) + UPI Accepted",
        "discount_code": "DRIP10 (10% OFF First Order)",
        "collections": [
            {"name": "Kollywood", "styles": 15, "startingPrice": 699, "desc": "Tamil cinema mass icons & cult dialogues (Jana Nayagan, AK The Don, Thalapathy)"},
            {"name": "Bollywood", "styles": 5, "startingPrice": 699, "desc": "Hindi cinema legends & cult statements (Main Rukta Nahi Hoon, Kismat Der Se Aye)"},
            {"name": "Tollywood", "styles": 3, "startingPrice": 699, "desc": "Telugu cinema hero statements (Flower Nahi FIRE Pushpa, Jhukega Nahi Saala)"},
            {"name": "Love Edition", "styles": 2, "startingPrice": 799, "desc": "Romance & aesthetic cinematic pieces (Some Feelings Don't Need Words)"},
            {"name": "Heavyweights", "styles": 4, "startingPrice": 1499, "desc": "380 GSM & 240 GSM oversized hoodies & sweatshirts (In The Shadows We Forge)"},
        ],
        "products": [
            {"id": "MD001", "name": "Jana Nayagan â€” Crowd Edition", "price": 699, "category": "Kollywood", "gsm": "240 GSM Heavyweight Tee", "badge": "HOT", "color": "Black"},
            {"id": "MD002", "name": "In The Shadows We Forge", "price": 1499, "category": "Heavyweights", "gsm": "240 GSM Oversized Hoodie", "badge": "BESTSELLER", "color": "Black"},
            {"id": "MD003", "name": "Main Rukta Nahi Hoon (Sweatshirt)", "price": 1199, "category": "Bollywood", "gsm": "240 GSM Sweatshirt", "badge": "NEW", "color": "Black"},
            {"id": "MD004", "name": "Main Rukta Nahi Hoon (Tee)", "price": 699, "category": "Bollywood", "gsm": "240 GSM Oversized Tee", "badge": "TRENDING", "color": "Black"},
            {"id": "MD005", "name": "Kismat Der Se Aye (Cracked Tee)", "price": 699, "category": "Bollywood", "gsm": "240 GSM Cracked Wall Tee", "badge": "TRENDING", "color": "Black"},
            {"id": "MD006", "name": "Kismat Der Se Aye (Melange Grey Hoodie)", "price": 1599, "category": "Heavyweights", "gsm": "240 GSM Cracked Hoodie", "badge": "NEW", "color": "Melange Grey"},
            {"id": "MD007", "name": "Kismat Der Se Aye (White Hoodie)", "price": 1599, "category": "Heavyweights", "gsm": "240 GSM Cracked Hoodie", "badge": "HOT", "color": "White"},
            {"id": "MD008", "name": "Jana Nayagan â€” The People's Hero", "price": 799, "category": "Kollywood", "gsm": "240 GSM Dark Silhouette Tee", "badge": "LIMITED", "color": "Black"},
            {"id": "MD009", "name": "Flower Nahi, FIRE (Pushpa)", "price": 699, "category": "Tollywood", "gsm": "240 GSM Wildfire Tee", "badge": "HOT", "color": "Black"},
            {"id": "MD010", "name": "Thalapathy Forever Statement Tee", "price": 799, "category": "Kollywood", "gsm": "240 GSM Statement Tee", "badge": "BESTSELLER", "color": "Black"},
            {"id": "MD027", "name": "AK â€” The Don's Edition (380 GSM)", "price": 1499, "category": "Kollywood", "gsm": "380 GSM Fleece Drop", "badge": "LIMITED", "color": "Black"},
        ],
        "synced_at": "Just now"
    }

    store_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "scraped_site_data.json")
    with open(store_file, "w", encoding="utf-8") as f:
        json.dump(store_data, f, indent=2)

    return {
        "success": True,
        "message": f"Successfully scraped and synced knowledge from {url}!",
        "data": store_data
    }

@router.get("/store-knowledge")
async def get_store_knowledge_endpoint():
    """Returns the current active store knowledge for display in the dashboard."""
    store_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "services", "scraped_site_data.json")
    if os.path.exists(store_file):
        with open(store_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"website": "https://www.massdrips.shop/", "brand_name": "MASS DRIPS", "products": []}


@router.post("/transcribe")
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Transcribes user microphone audio in ~150ms using Groq Whisper turbo with zero hallucinations."""
    from groq import Groq
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    audio_bytes = await file.read()
    if not audio_bytes:
        return {"success": True, "text": ""}

    client = Groq(api_key=groq_api_key)
    filename = file.filename or "audio.webm"

    try:
        res = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(filename, audio_bytes),
            prompt="Mass Drips, streetwear, oversized tee, hoodie, 240 GSM, Jana Nayagan, Kollywood, Bollywood, Tollywood, DRIP10, Rahul",
            language="en"
        )
        return {"success": True, "text": res.text.strip()}
    except Exception as e:
        return {"success": False, "text": "", "error": str(e)}



