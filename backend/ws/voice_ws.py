"""
backend/ws/voice_ws.py

WebSocket handler for the real-time voice pipeline.

ARCHITECTURE OVERVIEW (for future agents):
==========================================
This is the entry point for all live voice calls. Each WebSocket connection
represents one active call session between the AI agent and one lead.

Connection URL pattern:
  ws://localhost:8000/ws/voice/{tenant_id}/{lead_id}

Pipeline (all stages run as concurrent asyncio Tasks per session):

  Client (browser/Twilio)
      |-- binary frames (raw 16kHz 16-bit mono PCM) -->
  [VAD: Silero ONNX]        -- detects speech boundaries
      |-- utterance PCM blob -->
  [STT: Faster-Whisper]     -- transcribes speech to text
      |-- transcript text -->
  [Laya Router]             -- intent classification (in llm_worker)
      |-- fast bypass / LLM call -->
  [LLM: Groq / Ollama]      -- generates response (streaming early-emit)
      |-- response sentences -->
  [TTS: Kokoro / Edge-TTS]  -- synthesizes each sentence to PCM
      |-- PCM chunks -->
      |-- binary frames --> Client
      |-- JSON events   --> Client (transcript, agent_text, audio_start/end)

Session lifecycle:
  1. WebSocket connect -> build system prompt from DB
  2. Start 4 async pipeline workers (STT, LLM, TTS, audio sender)
  3. Receive loop: binary audio -> VAD, text -> direct transcript queue
  4. On disconnect: graceful shutdown of all workers in pipeline order
  5. Post-call: score lead, update MongoDB, trigger follow-up message

JSON message protocol (server -> client):
  {"type": "connected", "session_id": "..."}    -- on connect
  {"type": "transcript", "text": "..."}          -- user speech recognized
  {"type": "agent_text", "text": "..."}          -- agent about to speak
  {"type": "audio_start"}                        -- audio stream starting
  {"type": "audio_end"}                          -- audio stream complete
  {"type": "call_ended", "score": 75, ...}       -- on disconnect (post-call)
  {"type": "ack", "received": {...}}             -- control message receipt

Binary message protocol (server -> client):
  Raw 16kHz 16-bit mono PCM bytes, streamed in 640-byte (20ms) chunks.
  Client must buffer and play these sequentially.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agent.llm import llm_worker
from backend.agent.prompts import build_system_prompt
from backend.services import (
    get_tenant_persona,
    get_lead_context,
    get_products_for_tenant,
    update_lead_after_call,
)
from backend.voice.stt import stt_worker
from backend.voice.tts import tts_worker
from backend.voice.vad import VoiceActivityDetector

logger = logging.getLogger(__name__)

router = APIRouter()

# 20ms of 16kHz 16-bit mono PCM = 640 bytes per chunk
# Smaller chunks = lower perceived latency but more WS frames overhead
AUDIO_CHUNK_SIZE = 640


@router.websocket("/ws/voice/{tenant_id}/{lead_id}")
async def voice_websocket(
    websocket: WebSocket,
    tenant_id: str,
    lead_id: str,
):
    """
    Main WebSocket handler for a live AI voice call session.

    Args:
        tenant_id: MongoDB ObjectId of the tenant (brand using VoxSales).
        lead_id:   MongoDB ObjectId of the lead being called.

    The handler:
      1. Accepts the connection and sends a "connected" event
      2. Builds the system prompt from DB (tenant config + lead context + products)
      3. Spins up 4 async pipeline workers
      4. Runs the main receive loop (audio bytes or text commands)
      5. On disconnect: tears down pipeline and runs post-call actions
    """
    session_id = str(uuid.uuid4())[:8]
    call_transcript: list[dict] = []   # accumulated for post-call scoring

    await websocket.accept()
    logger.info("[%s] WebSocket connected for %s/%s", session_id, tenant_id, lead_id)

    # ── Send connected event ─────────────────────────────────────────────────
    await websocket.send_text(json.dumps({
        "type":       "connected",
        "session_id": session_id,
        "timestamp":  datetime.utcnow().isoformat(),
    }))

    # ── Build system prompt from DB ──────────────────────────────────────────
    # These DB calls happen once per session at connect time.
    # The prompt is static for the full call duration (Laya hints are appended
    # per-turn inside llm_worker without rebuilding from DB).
    try:
        tenant_config = await get_tenant_persona(tenant_id)
        lead_info     = await get_lead_context(lead_id, tenant_id)
        products      = await get_products_for_tenant(tenant_id, in_stock_only=True, limit=10)
    except Exception as e:
        logger.warning("[%s] DB lookup failed (%s) -- using defaults", session_id, e)
        tenant_config = {}
        lead_info     = {}
        products      = []

    system_prompt = build_system_prompt(
        tenant_config=tenant_config,
        lead_info=lead_info,
        products=products,
    )
    logger.info(
        "[%s] System prompt built: %d chars, lead=%s",
        session_id, len(system_prompt),
        lead_info.get("name", "unknown") if lead_info else "unknown",
    )

    # ── Per-session async queues (pipeline connectors) ───────────────────────
    # Each queue is the "pipe" between two pipeline stages.
    # Sentinels (None) propagate through the pipeline in order on disconnect.
    stt_queue        = asyncio.Queue()   # VAD     --> STT worker
    transcript_queue = asyncio.Queue()   # STT     --> LLM worker
    response_queue   = asyncio.Queue()   # LLM     --> TTS worker
    audio_queue      = asyncio.Queue()   # TTS     --> audio sender

    current_turn = [0]
    interrupted_turn = [-1]

    def handle_barge_in():
        interrupted_turn[0] = current_turn[0]
        logger.info("[%s] User barge-in detected during turn %d", session_id, current_turn[0])

    # ── VAD instance ─────────────────────────────────────────────────────────
    # One SileroVAD instance per session (maintains per-call LSTM state).
    vad = VoiceActivityDetector(output_queue=stt_queue, on_speech_start=handle_barge_in)

    # ── Background pipeline workers ──────────────────────────────────────────
        # Outbound live call opening greeting
    lead_name = lead_info.get("name", "Rahul") if lead_info else "Rahul"
    if not lead_name or lead_name in ("Customer", "there", "unknown"):
        lead_name = "Rahul"
    else:
        lead_name = lead_name.split()[0]
    agent_name = tenant_config.get("name", "Alex") if tenant_config else "Alex"
    brand_name = tenant_config.get("brand", "Mass Drips") if tenant_config else "Mass Drips"
    greeting_text = (
        f"Hey {lead_name}! This is {agent_name} calling from {brand_name} in Chennai. "
        f"Did I catch you at an okay time for 30 seconds? Also, are you comfortable in English, or would you prefer Hindi or Tamil?"
    )

    stt_task = asyncio.create_task(
        stt_worker(
            stt_queue=stt_queue,
            transcript_queue=transcript_queue,
            tenant_id=tenant_id,
            lead_id=lead_id,
            websocket=websocket,
            call_transcript=call_transcript,
        )
    )

    llm_task = asyncio.create_task(
        llm_worker(
            transcript_queue=transcript_queue,
            response_queue=response_queue,
            system_prompt=system_prompt,
            tenant_id=tenant_id,
            lead_id=lead_id,
            initial_greeting=greeting_text,
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

    # ── Audio sender: streams PCM back to client ─────────────────────────────
    async def send_audio_loop():
        """
        Dequeues synthesized PCM audio chunks from audio_queue and streams
        them back to the client as binary WebSocket frames.

        Sends JSON event messages (agent_text, audio_start, audio_end) around
        each audio burst so the client knows when to start/stop playback.

        Also appends agent responses to call_transcript for post-call scoring.
        """
        while True:
            item = await audio_queue.get()
            if item is None:
                break

            pcm  = item["pcm"]
            text = item["text"]

            # Append to call transcript for post-call analysis
            call_transcript.append({"role": "assistant", "text": text})

            try:
                # Notify client of agent text (for transcript display in UI)
                await websocket.send_text(json.dumps({
                    "type": "agent_text",
                    "text": text,
                }))
                await websocket.send_text(json.dumps({"type": "audio_start"}))

                current_turn[0] += 1
                this_turn = current_turn[0]

                STREAM_CHUNK = 3200
                for i in range(0, len(pcm), STREAM_CHUNK):
                    if this_turn <= interrupted_turn[0]:
                        logger.info("[%s] Audio play cancelled due to barge-in on turn %d", session_id, this_turn)
                        break
                    await websocket.send_bytes(pcm[i : i + STREAM_CHUNK])
                    await asyncio.sleep(0)  # yield event loop without artificial delay

                if this_turn > interrupted_turn[0]:
                    await websocket.send_text(json.dumps({"type": "audio_end"}))

                logger.info(
                    "[%s] Audio sent: '%s...' (%d bytes)",
                    session_id, text[:40], len(pcm),
                )
            except Exception as e:
                logger.error("[%s] Audio send error: %s", session_id, e)
                break

            audio_queue.task_done()

    audio_task = asyncio.create_task(send_audio_loop())

    # Immediate zero-latency greeting delivery using cached audio
    from backend.voice.tts import get_cached_greeting_pcm
    greeting_pcm = await get_cached_greeting_pcm(greeting_text)
    if greeting_pcm:
        await audio_queue.put({
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "pcm": greeting_pcm,
            "text": greeting_text,
        })
    else:
        await response_queue.put({
            "tenant_id": tenant_id,
            "lead_id": lead_id,
            "user_text": "[CALL_STARTED]",
            "response": greeting_text,
        })

    # ── Main receive loop ────────────────────────────────────────────────────
    # Handles two input types:
    #   1. Binary: raw PCM bytes from browser microphone --> VAD
    #   2. Text:   JSON control messages or raw text for testing --> transcript queue
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                logger.info("[%s] WebSocket disconnect signal received.", session_id)
                break

            # Binary audio: send directly to VAD
            if "bytes" in message and message["bytes"] is not None:
                await vad.feed(message["bytes"])

            # Text: control message or test input
            elif "text" in message and message["text"] is not None:
                raw = message["text"]
                try:
                    payload = json.loads(raw)
                    msg_type = payload.get("type", "unknown")
                    logger.debug("[%s] Control: %s", session_id, msg_type)
                    await websocket.send_text(
                        json.dumps({"type": "ack", "received": payload})
                    )
                except json.JSONDecodeError:
                    # Plain text --> treat as direct user speech (testing path)
                    logger.info("[%s] Text input: '%s'", session_id, raw[:60])

                    # Relay transcript event to client UI
                    await websocket.send_text(
                        json.dumps({"type": "transcript", "text": raw})
                    )
                    # Append to transcript log
                    call_transcript.append({"role": "user", "text": raw})

                    # Push directly to transcript queue (bypasses VAD+STT)
                    await transcript_queue.put({
                        "tenant_id":  tenant_id,
                        "lead_id":    lead_id,
                        "transcript": raw,
                    })

    except WebSocketDisconnect:
        logger.info("[%s] WebSocket disconnected.", session_id)

    except Exception as e:
        logger.error("[%s] Unexpected error in receive loop: %s", session_id, e)

    finally:
        # ── Graceful pipeline teardown (in pipeline order) ────────────────
        # Each None sentinel propagates downstream automatically via worker logic.
        logger.info("[%s] Tearing down pipeline...", session_id)

        await vad.flush()                        # flush remaining VAD audio

        await stt_queue.put(None)                # signal STT to stop
        await stt_task                           # wait for STT to finish

        await transcript_queue.put(None)         # signal LLM to stop
        await llm_task                           # wait for LLM to finish

        # LLM worker puts None into response_queue automatically
        await tts_task                           # wait for TTS to finish

        # TTS worker puts None into audio_queue automatically
        await audio_task                         # wait for audio sender to finish

        logger.info("[%s] Pipeline stopped. Running post-call actions...", session_id)

        # ── Post-call: score lead + update MongoDB ────────────────────────
        await _post_call_actions(
            session_id=session_id,
            tenant_id=tenant_id,
            lead_id=lead_id,
            call_transcript=call_transcript,
            websocket=websocket,
        )

        logger.info("[%s] Session fully cleaned up.", session_id)


async def _post_call_actions(
    session_id: str,
    tenant_id: str,
    lead_id: str,
    call_transcript: list,
    websocket: WebSocket,
) -> None:
    """
    Run post-call processing after the WebSocket disconnects.

    Actions:
      1. Score the lead using Laya fast scoring (~5ms)
      2. Update lead record in MongoDB (score, outcome, last_called)
      3. Send call_ended event to client (if still connected)
      4. Log the call in call_logs collection (if implemented)

    This runs in the finally block of the main handler -- errors here are
    logged but do not raise to avoid breaking the graceful shutdown flow.

    Args:
        session_id:      Short session identifier for logging.
        tenant_id:       Tenant MongoDB ID.
        lead_id:         Lead MongoDB ID.
        call_transcript: List of {role, text} dicts from the full call.
        websocket:       WebSocket reference (may already be closed).
    """
    if not call_transcript:
        logger.info("[%s] Empty transcript -- skipping post-call scoring.", session_id)
        return

    try:
        from backend.agent.laya_router import laya_engine
        scoring_result = laya_engine.evaluate_lead_score_fast(call_transcript)

        logger.info(
            "[%s] Post-call score: %d/100, outcome=%s, sentiment=%s",
            session_id,
            scoring_result["score"],
            scoring_result["outcome"],
            scoring_result["sentiment"],
        )

        # Update lead in MongoDB
        call_summary = f"Auto-scored: {scoring_result['outcome']} | " \
                       f"Score: {scoring_result['score']}/100 | " \
                       f"Intent: {scoring_result['laya_intent']}"

        from bson import ObjectId
        if ObjectId.is_valid(lead_id):
            await update_lead_after_call(
                lead_id=lead_id,
                summary=call_summary,
                outcome=scoring_result["outcome"],
                score_delta=scoring_result["score"] - 40,
            )
        else:
            logger.info("[%s] Demo lead ID '%s' - skipping MongoDB lead update.", session_id, lead_id)

        # Try to notify client of call result (they may already be disconnected)
        try:
            await websocket.send_text(json.dumps({
                "type":      "call_ended",
                "score":     scoring_result["score"],
                "outcome":   scoring_result["outcome"],
                "sentiment": scoring_result["sentiment"],
                "turns":     len(call_transcript),
            }))
        except Exception:
            pass  # Client already disconnected -- expected

    except Exception as e:
        logger.error("[%s] Post-call actions failed: %s", session_id, e)
