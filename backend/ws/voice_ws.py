"""
backend/ws/voice_ws.py

WebSocket endpoint for real-time audio streaming.

Data flow per session:
    Browser/Phone
        │  binary PCM frames (16kHz, 16-bit, mono)
        ▼
    voice_ws (this file)
        │  raw bytes
        ▼
    VoiceActivityDetector   [VAD — Silero ONNX]
        │  complete utterance bytes
        ▼
    stt_queue (asyncio.Queue)
        │
    stt_worker task         [Whisper STT]
        │  {"tenant_id", "lead_id", "transcript"}
        ▼
    transcript_queue (asyncio.Queue)
        │
    [Phase 3: LLM agent — coming next]
"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.voice.vad import VoiceActivityDetector
from backend.voice.stt import stt_worker

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/voice/{tenant_id}/{lead_id}")
async def voice_websocket(
    websocket: WebSocket,
    tenant_id: str,
    lead_id: str,
):
    """
    Multi-tenant WebSocket endpoint.

    URL params:
        tenant_id — Identifies the SaaS client.
        lead_id   — Identifies the specific call/lead.

    Message types:
        Binary  → raw PCM audio bytes → VAD → STT
        Text    → JSON control messages (e.g. {"type": "start_call"})
    """
    await websocket.accept()
    logger.info(f"[{tenant_id}/{lead_id}] WebSocket connected.")

    # ── Per-session queues ──────────────────────────────────────────────────
    stt_queue        = asyncio.Queue()   # VAD  --> STT worker
    transcript_queue = asyncio.Queue()   # STT  --> LLM agent (Phase 3)

    # ── Voice Activity Detector ─────────────────────────────────────────────
    vad = VoiceActivityDetector(output_queue=stt_queue)

    # ── STT background worker ───────────────────────────────────────────────
    stt_task = asyncio.create_task(
        stt_worker(
            stt_queue=stt_queue,
            transcript_queue=transcript_queue,
            tenant_id=tenant_id,
            lead_id=lead_id,
        )
    )

    # ── Transcript relay task (sends transcript back over WS for now) ───────
    async def relay_transcripts():
        """Relay transcription results back to the client over WebSocket."""
        while True:
            result = await transcript_queue.get()
            if result is None:
                break
            msg = {
                "type":       "transcript",
                "tenant_id":  result["tenant_id"],
                "lead_id":    result["lead_id"],
                "text":       result["transcript"],
            }
            try:
                await websocket.send_text(json.dumps(msg))
                logger.info(
                    f"[{tenant_id}/{lead_id}] Transcript sent: "
                    f"'{result['transcript']}'"
                )
            except Exception:
                break
            transcript_queue.task_done()

    relay_task = asyncio.create_task(relay_transcripts())

    # ── Main receive loop ───────────────────────────────────────────────────
    try:
        while True:
            message = await websocket.receive()

            # Binary: raw PCM audio
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
                    # Echo back for now; Phase 3 will handle commands
                    await websocket.send_text(
                        json.dumps({"type": "ack", "received": payload})
                    )
                except json.JSONDecodeError:
                    # Plain text — legacy support from test_ws_client
                    await websocket.send_text(
                        f"Server acknowledged: {message['text']}"
                    )

    except WebSocketDisconnect:
        logger.info(f"[{tenant_id}/{lead_id}] WebSocket disconnected.")

    finally:
        # ── Graceful teardown ───────────────────────────────────────────────
        await vad.flush()                   # Flush any trailing speech
        await stt_queue.put(None)           # Signal STT worker to stop
        await stt_task                      # Wait for STT to finish
        await transcript_queue.put(None)    # Signal relay to stop
        relay_task.cancel()
        logger.info(f"[{tenant_id}/{lead_id}] Session cleaned up.")
