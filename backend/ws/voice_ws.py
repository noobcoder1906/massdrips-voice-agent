"""
backend/ws/voice_ws.py

WebSocket endpoint for real-time AI voice conversation — Phase 4.

Full pipeline per session:
    Client (phone/browser)
        │  binary PCM frames (16kHz, 16-bit, mono)
        ▼
    VoiceActivityDetector   [VAD — Silero ONNX]
        │  complete utterance bytes
        ▼
    stt_queue ──► stt_worker      [Faster-Whisper STT]
        │  {"transcript": str}
        ▼
    transcript_queue ──► llm_worker  [Ollama streaming LLM]
        │  {"response": str}
        ▼
    response_queue ──► tts_worker    [Kokoro ONNX TTS]
        │  raw PCM bytes (per sentence — streaming)
        ▼
    audio_queue ──► WebSocket binary frames back to client
        │
    Client plays audio → user hears AI voice response
"""

import asyncio
import json
import logging
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.voice.vad import VoiceActivityDetector
from backend.voice.stt import stt_worker
from backend.voice.tts import tts_worker
from backend.agent.llm import llm_worker
from backend.agent.prompts import build_system_prompt, DEFAULT_PERSONA

logger = logging.getLogger(__name__)

router = APIRouter()

# Chunk size for streaming audio back (20ms @ 16kHz = 640 bytes)
AUDIO_CHUNK_SIZE = 640


def _get_tenant_config(tenant_id: str) -> dict:
    """TODO Phase 5: Load from MongoDB. Returns default config for now."""
    return {**DEFAULT_PERSONA, "tenant_id": tenant_id}


def _get_lead_info(lead_id: str) -> dict:
    """TODO Phase 5: Load from MongoDB. Returns placeholder for now."""
    return {
        "id":    lead_id,
        "name":  "Customer",
        "interests": [],
        "last_interaction_summary": "",
    }


def _get_products(tenant_id: str) -> list:
    """TODO Phase 5: Load from MongoDB product catalog."""
    return []


@router.websocket("/ws/voice/{tenant_id}/{lead_id}")
async def voice_websocket(
    websocket: WebSocket,
    tenant_id: str,
    lead_id: str,
):
    """
    Multi-tenant WebSocket endpoint — Phase 4 (Full Voice Pipeline).

    Incoming:  Binary PCM audio frames from client
    Outgoing:  Binary PCM audio frames (AI voice) + JSON event messages

    JSON messages sent to client:
      {"type": "transcript",      "text": "..."}  — what user said
      {"type": "agent_text",      "text": "..."}  — what agent will say
      {"type": "audio_start"}                      — audio is about to stream
      {"type": "audio_end"}                        — audio stream complete
      {"type": "ack",             "received": ...} — control message ack
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
    logger.info(
        f"[{tenant_id}/{lead_id}] System prompt built ({len(system_prompt)} chars)"
    )

    # ── Per-session async queues ────────────────────────────────────────────
    stt_queue        = asyncio.Queue()  # VAD  → STT worker
    transcript_queue = asyncio.Queue()  # STT  → LLM worker
    response_queue   = asyncio.Queue()  # LLM  → TTS worker
    audio_queue      = asyncio.Queue()  # TTS  → WebSocket audio sender

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

    tts_task = asyncio.create_task(
        tts_worker(
            response_queue=response_queue,
            audio_queue=audio_queue,
            tenant_id=tenant_id,
            lead_id=lead_id,
        )
    )

    # ── Audio sender: streams PCM back to client in chunks ──────────────────
    async def send_audio():
        """
        Pulls synthesized PCM audio from audio_queue and sends it back to
        the client as binary WebSocket frames.

        Sends JSON event messages around each audio burst so the client
        knows when to start/stop buffering and playing audio.
        """
        while True:
            item = await audio_queue.get()
            if item is None:
                break

            pcm    = item["pcm"]
            text   = item["text"]
            t_id   = item["tenant_id"]
            l_id   = item["lead_id"]

            try:
                # Signal to client: agent text + audio incoming
                await websocket.send_text(json.dumps({
                    "type": "agent_text",
                    "text": text,
                }))
                await websocket.send_text(json.dumps({"type": "audio_start"}))

                # Stream PCM in 20ms chunks for low-latency playback
                for i in range(0, len(pcm), AUDIO_CHUNK_SIZE):
                    chunk = pcm[i:i + AUDIO_CHUNK_SIZE]
                    await websocket.send_bytes(chunk)
                    # Tiny yield so incoming messages aren't blocked
                    await asyncio.sleep(0)

                await websocket.send_text(json.dumps({"type": "audio_end"}))
                logger.info(
                    f"[{t_id}/{l_id}] Audio sent: "
                    f"'{text[:50]}' ({len(pcm)} bytes)"
                )
            except Exception as e:
                logger.error(f"Audio send error: {e}")
                break

            audio_queue.task_done()

    audio_task = asyncio.create_task(send_audio())

    # ── STT transcript relay (send transcript text to client as JSON) ───────
    async def relay_transcript_events():
        """Forward transcript text events to the client for UI display."""
        # We hook into this by wrapping the transcript_queue indirectly.
        # The STT worker will push items; we intercept them here via a
        # separate monitoring approach in Phase 7 (dashboard).
        # For now, handled inline in the main receive loop below.
        pass

    # ── Main receive loop ───────────────────────────────────────────────────
    try:
        while True:
            message = await websocket.receive()

            # Binary: raw PCM audio bytes → VAD pipeline
            if "bytes" in message and message["bytes"] is not None:
                await vad.feed(message["bytes"])

            # Text: JSON control messages or direct text (for testing)
            elif "text" in message and message["text"] is not None:
                raw = message["text"]
                try:
                    payload = json.loads(raw)
                    msg_type = payload.get("type", "unknown")
                    logger.info(
                        f"[{tenant_id}/{lead_id}] Control msg: {msg_type}"
                    )
                    await websocket.send_text(
                        json.dumps({"type": "ack", "received": payload})
                    )
                except json.JSONDecodeError:
                    # Plain text input → treat as direct user speech transcript
                    # (used by test clients and dev tools)
                    logger.info(
                        f"[{tenant_id}/{lead_id}] Text input: '{raw[:60]}'"
                    )
                    await websocket.send_text(
                        json.dumps({"type": "transcript", "text": raw})
                    )
                    await transcript_queue.put({
                        "tenant_id":  tenant_id,
                        "lead_id":    lead_id,
                        "transcript": raw,
                    })

    except WebSocketDisconnect:
        logger.info(f"[{tenant_id}/{lead_id}] WebSocket disconnected.")

    finally:
        # ── Graceful teardown — in pipeline order ───────────────────────────
        await vad.flush()

        await stt_queue.put(None)        # → STT stop
        await stt_task

        await transcript_queue.put(None) # → LLM stop
        await llm_task

        # response_queue sentinel sent by llm_worker itself
        await tts_task

        # audio_queue sentinel sent by tts_worker itself
        await audio_task

        logger.info(f"[{tenant_id}/{lead_id}] Full session cleaned up. ✓")
