"""
backend/main.py

VoxSales Multi-Tenant AI Voice Agent Platform -- Phase 10 (Production-Ready).

Startup sequence:
  1. Connect MongoDB
  2. Pre-warm ALL models (Whisper STT, Chatterbox TTS, Silero VAD, Kokoro)
  3. Pre-synthesize greeting audio into cache
  4. Start campaign scheduler
  --> Server ready with ZERO cold-start latency on first call
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.database import connect_to_mongo, close_mongo_connection
from backend.ws.voice_ws import router as voice_router
from backend.routes.routes import tenant_router, lead_router, product_router
from backend.routes.campaigns import router as campaign_router
from backend.routes.smart import router as smart_router
from backend.routes.calls import router as calls_router
from backend.routes.webhooks import router as webhooks_router
from backend.campaigns.scheduler import scheduler_instance

logger = logging.getLogger(__name__)


async def _warmup_all_models():
    """
    Pre-warm ALL inference models before the first call arrives.

    This is the CRITICAL fix for cold-start latency. Without this, the first
    call triggers model loading which can take 5-30 seconds. With warmup, all
    models are hot and ready by the time the server reports 'Application startup complete'.

    Models warmed up:
      1. Silero VAD (ONNX, ~10ms load)
      2. Whisper STT -- local fallback model (faster-whisper, ~2s)
      3. Chatterbox TTS -- voice clone model (GPU, ~5-15s on T4)
      4. Kokoro TTS -- local neural voice (ONNX, ~1s)
      5. Greeting audio cache -- pre-synthesized greeting PCM
    """
    logger.info("=" * 60)
    logger.info("WARMUP: Pre-loading all models...")
    logger.info("=" * 60)

    # 1. VAD -- just importing/instantiating triggers ONNX model load
    try:
        from backend.voice.vad import SileroVAD
        _ = SileroVAD()
        logger.info("WARMUP [1/5] Silero VAD: OK")
    except Exception as e:
        logger.warning("WARMUP [1/5] Silero VAD: FAILED - %s", e)

    # 2. Whisper local fallback
    try:
        from backend.voice.stt import WhisperSTT
        _ = WhisperSTT.get_local_model()
        logger.info("WARMUP [2/5] Whisper STT: OK")
    except Exception as e:
        logger.warning("WARMUP [2/5] Whisper STT: FAILED (Groq will be primary) - %s", e)

    # 3. Chatterbox TTS -- voice clone (most important, slowest to load)
    try:
        from backend.voice.chatterbox_pipeline import _get_chatterbox
        loop = asyncio.get_event_loop()
        model = await _get_chatterbox()
        if model is not None:
            logger.info("WARMUP [3/5] Chatterbox voice clone: OK (GPU loaded)")
        else:
            logger.warning("WARMUP [3/5] Chatterbox voice clone: model=None (will use edge_tts fallback)")
    except Exception as e:
        logger.warning("WARMUP [3/5] Chatterbox TTS: FAILED - %s", e)

    # 4. Kokoro TTS
    try:
        from backend.voice.tts import KokoroTTS
        _ = KokoroTTS._get_pipeline()
        logger.info("WARMUP [4/5] Kokoro TTS: OK")
    except Exception as e:
        logger.warning("WARMUP [4/5] Kokoro TTS: FAILED - %s", e)

    # 5. Pre-synthesize greeting into cache (zero-latency first response)
    try:
        from backend.voice.tts import get_cached_greeting_pcm
        greeting = "Hey! This is Sai from Mass Drips. How are you doing today?"
        pcm = await get_cached_greeting_pcm(greeting)
        if pcm:
            logger.info("WARMUP [5/5] Greeting cache: OK (%d bytes pre-synthesized)", len(pcm))
        else:
            logger.warning("WARMUP [5/5] Greeting cache: empty PCM returned")
    except Exception as e:
        logger.warning("WARMUP [5/5] Greeting cache: FAILED - %s", e)

    logger.info("=" * 60)
    logger.info("WARMUP COMPLETE -- Server is hot and ready!")
    logger.info("=" * 60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup --> yield --> shutdown."""
    await connect_to_mongo()
    await _warmup_all_models()
    scheduler_instance.start()
    yield
    scheduler_instance.stop()
    await close_mongo_connection()


app = FastAPI(
    title="VoxSales Public API",
    description="Multi-Tenant AI Voice Sales Agent Platform -- Sai (Mass Drips)",
    version="10.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket (voice pipeline)
app.include_router(voice_router)

# REST API routes (v1)
app.include_router(tenant_router)
app.include_router(lead_router)
app.include_router(product_router)
app.include_router(campaign_router)
app.include_router(smart_router)
app.include_router(calls_router)
app.include_router(webhooks_router)

# Static Frontend & SPA Serving
root_dir = os.path.dirname(os.path.dirname(__file__))
dist_path = os.path.join(root_dir, "voxsales-app", "dist")
legacy_frontend_path = os.path.join(root_dir, "frontend")

if os.path.exists(dist_path):
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith(("docs", "redoc", "openapi.json", "api", "ws")):
            return None
        file_path = os.path.join(dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))

elif os.path.exists(legacy_frontend_path):
    app.mount("/static", StaticFiles(directory=legacy_frontend_path), name="static")

    @app.get("/styles.css", include_in_schema=False)
    async def serve_css():
        return FileResponse(os.path.join(legacy_frontend_path, "styles.css"))

    @app.get("/app.js", include_in_schema=False)
    async def serve_js():
        return FileResponse(os.path.join(legacy_frontend_path, "app.js"))

    @app.get("/dashboard", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(os.path.join(legacy_frontend_path, "index.html"))
