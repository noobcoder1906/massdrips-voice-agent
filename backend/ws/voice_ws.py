"""
backend/ws/voice_ws.py

WebSocket endpoint for real-time audio streaming — Phase 3.

Full pipeline per session:
    Browser/Phone
        │  binary PCM frames (16kHz, 16-bit, mono)
        ▼
    VoiceActivityDetector   [VAD — Silero ONNX]
        │  complete utterance bytes
        ▼
    stt_queue ──► stt_worker      [Faster-Whisper STT]
        │  {"transcript": str}
        ▼
    transcript_queue ──► llm_worker  [Ollama LLM — streaming]
        │  {"response": str}
        ▼
    response_queue ──► WebSocket relay  (Phase 4: → TTS)
"""

import asyncio
import json
import logging
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.voice.vad import VoiceActivityDetector
from backend.voice.stt import stt_worker
from backend.agent.llm import llm_worker
from backend.agent.prompts import build_system_prompt, DEFAULT_PERSONA

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_tenant_config(tenant_id: str) -> dict:
    """
    TODO (Phase 5): Load from MongoDB tenant collection.
    For now returns default Mass Drips config.
    """
    return {**DEFAULT_PERSONA, "tenant_id": tenant_id}


def _get_lead_info(lead_id: str) -> dict:
    """
    TODO (Phase 5): Load from MongoDB leads collection.
    For now returns placeholder lead data.
    """
    return {
        "id":    lead_id,
        "name":  "Customer",
        "interests": [],
        "last_interaction_summary": "",
    }


def _get_products(tenant_id: str) -> list:
    """
    TODO (Phase 5): Load from MongoDB product catalog.
    For now returns empty — agent will still work generically.
    """
    return []


@router.websocket("/ws/voice/{tenant_id}/{lead_id}")
async def voice_websocket(
    websocket: WebSocket,
    tenant_id: str,
    lead_id: str,
):
    """
    Multi-tenant WebSocket endpoint — Phase 3.
    Full pipeline: Audio → VAD → STT → LLM → WebSocket response.

    URL params:
        tenant_id — Identifies the SaaS client / brand.
        lead_id   — Identifies the specific call/lead.
    """
    await websocket.accept()
    logger.info(f"[{tenant_id}/{lead_id}] WebSocket connected.")

    # ── Build tenant system prompt ──────────────────────────────────────────
    tenant_config = _get_tenant_config(tenant_id)
    lead_info     = _get_lead_info(lead_id)
    products      = _get_products(tenant_id)
    system_prompt = build_system_prompt(
        tenant_config=tenant_config,
        lead_info=lead_info,
        products=products,
    )
    logger.info(f"[{tenant_id}/{lead_id}] System prompt built ({len(system_prompt)} chars)")

    # ── Per-session async queues ────────────────────────────────────────────
    stt_queue        = asyncio.Queue()  # VAD  → STT worker
    transcript_queue = asyncio.Queue()  # STT  → LLM worker
    response_queue   = asyncio.Queue()  # LLM  → WS relay (Phase 4: → TTS)

    # ── VAD instance ────────────────────────────────────────────────────────
    vad = VoiceActivityDetector(output_queue=stt_queue)

    # ── Background workers ──────────────────────────────────────────────────
    stt_task = asyncio.create_task(
        stt_worker(
            stt_queue=stt_queue,
            transcript_queue=transcript_queue,
            tenant_id=tenant_id,
            lead_id=lead_id,
        )
    )

    llm_task = asyncio.create_task(
        llm_worker(
            transcript_queue=transcript_queue,
            response_queue=response_queue,
            system_prompt=system_prompt,
            tenant_id=tenant_id,
            lead_id=lead_id,
        )
    )

    # ── Response relay: sends LLM reply back to client over WebSocket ───────
    async def relay_responses():
        while True:
            result = await response_queue.get()
            if result is None:
                break
            msg = {
                "type":       "agent_response",
                "tenant_id":  result["tenant_id"],
                "lead_id":    result["lead_id"],
                "user_said":  result["user_text"],
                "agent_said": result["response"],
            }
            try:
                await websocket.send_text(json.dumps(msg))
                logger.info(
                    f"[{tenant_id}/{lead_id}] "
                    f"User: '{result['user_text']}' | "
                    f"Agent: '{result['response'][:80]}...'"
                )
            except Exception:
                break
            response_queue.task_done()

    relay_task = asyncio.create_task(relay_responses())

    # ── Main receive loop ───────────────────────────────────────────────────
    try:
        while True:
            message = await websocket.receive()

            # Binary: raw PCM audio bytes → VAD pipeline
            if "bytes" in message and message["bytes"] is not None:
                await vad.feed(message["bytes"])

            # Text: JSON control messages
            elif "text" in message and message["text"] is not None:
                try:
                    payload = json.loads(message["text"])
                    msg_type = payload.get("type", "unknown")
                    logger.info(
                        f"[{tenant_id}/{lead_id}] Control msg: {msg_type}"
                    )
                    await websocket.send_text(
                        json.dumps({"type": "ack", "received": payload})
                    )
                except json.JSONDecodeError:
                    # Legacy plain text (e.g. from test client)
                    # Route as direct user message to LLM
                    await transcript_queue.put({
                        "tenant_id":  tenant_id,
                        "lead_id":    lead_id,
                        "transcript": message["text"],
                    })

    except WebSocketDisconnect:
        logger.info(f"[{tenant_id}/{lead_id}] WebSocket disconnected.")

    finally:
        # ── Graceful teardown ───────────────────────────────────────────────
        await vad.flush()
        await stt_queue.put(None)        # Stop STT worker
        await stt_task

        await transcript_queue.put(None) # Stop LLM worker
        await llm_task

        relay_task.cancel()
        logger.info(f"[{tenant_id}/{lead_id}] Session fully cleaned up.")
