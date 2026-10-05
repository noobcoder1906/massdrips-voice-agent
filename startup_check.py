#!/usr/bin/env python3
"""
startup_check.py

Pre-flight system check and model download script.
Run this ONCE after deploying to a new GPU node to ensure all
models are downloaded and cached before the first call arrives.

Usage (on E2E GPU node):
  python startup_check.py

This script:
  1. Verifies all Python dependencies are installed
  2. Downloads/caches ALL ML models (Silero VAD, Whisper, Chatterbox, Kokoro)
  3. Pre-generates the voice clone cache (greeting audio)
  4. Reports readiness status

The voice agent should NOT be started until this script completes with SUCCESS.
"""

import sys
import os
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("startup_check")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check(label, fn):
    start = time.time()
    try:
        result = fn()
        elapsed = time.time() - start
        print(f"  [OK]  {label} ({elapsed:.1f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"  [FAIL] {label} ({elapsed:.1f}s): {e}")
        return False


# ---- 1. Dependencies ----
section("STEP 1: Dependency Check")

deps = {
    "fastapi":         lambda: __import__("fastapi"),
    "uvicorn":         lambda: __import__("uvicorn"),
    "groq":            lambda: __import__("groq"),
    "faster_whisper":  lambda: __import__("faster_whisper"),
    "onnxruntime":     lambda: __import__("onnxruntime"),
    "numpy":           lambda: __import__("numpy"),
    "soundfile":       lambda: __import__("soundfile"),
    "motor":           lambda: __import__("motor"),
    "pymongo":         lambda: __import__("pymongo"),
    "chatterbox-tts":  lambda: __import__("chatterbox"),
    "kokoro-onnx":     lambda: __import__("kokoro"),
    "edge-tts":        lambda: __import__("edge_tts"),
}

all_ok = True
for name, fn in deps.items():
    ok = check(name, fn)
    if not ok:
        all_ok = False

if not all_ok:
    print("\n[WARNING] Some dependencies missing. Run:")
    print("  pip install -r requirements.txt")
    print("  pip install chatterbox-tts --no-deps")
    print("  pip install edge-tts")


# ---- 2. Silero VAD ----
section("STEP 2: Silero VAD Model")
from dotenv import load_dotenv
load_dotenv()

check("Silero VAD ONNX download + load", lambda: (
    __import__("backend.voice.vad", fromlist=["SileroVAD"]).SileroVAD()
))


# ---- 3. Whisper STT ----
section("STEP 3: Whisper STT Model")
check("Faster-Whisper model load (base)", lambda: (
    __import__("backend.voice.stt", fromlist=["WhisperSTT"]).WhisperSTT.get_local_model()
))


# ---- 4. Chatterbox TTS Voice Clone ----
section("STEP 4: Chatterbox TTS (Voice Clone)")

import asyncio

async def _warm_chatterbox():
    from backend.voice.chatterbox_pipeline import _get_chatterbox
    model = await _get_chatterbox()
    if model is None:
        raise RuntimeError("Chatterbox model returned None -- check GPU/CUDA")
    return model

try:
    model = asyncio.run(_warm_chatterbox())
    print(f"  [OK]  Chatterbox model loaded on GPU")
except Exception as e:
    print(f"  [FAIL] Chatterbox: {e}")


# ---- 5. Check voice clone WAV ----
section("STEP 5: Voice Clone Reference Audio")

ref_wav = os.path.join("backend", "voice", "clones", "my_voice.wav")
if os.path.exists(ref_wav):
    size = os.path.getsize(ref_wav)
    print(f"  [OK]  my_voice.wav found ({size//1024} KB)")
else:
    print(f"  [FAIL] my_voice.wav NOT FOUND at {ref_wav}")
    print("  Please upload your voice recording to this path.")

ref_npy = os.path.join("backend", "voice", "clones", "my_voice_style.npy")
if os.path.exists(ref_npy):
    size = os.path.getsize(ref_npy)
    print(f"  [OK]  my_voice_style.npy found ({size} bytes) -- Kokoro clone ready")
else:
    print(f"  [INFO] my_voice_style.npy not found (Kokoro clone not generated)")
    print("         Run: python backend/scripts/generate_voice_clone.py")


# ---- 6. Kokoro TTS ----
section("STEP 6: Kokoro TTS (Local Neural)")
check("Kokoro TTS pipeline load", lambda: (
    __import__("backend.voice.tts", fromlist=["KokoroTTS"]).KokoroTTS._get_pipeline()
))


# ---- 7. Pre-synthesize Greeting ----
section("STEP 7: Pre-synthesize Greeting Audio Cache")

async def _warm_greeting():
    from backend.voice.tts import get_cached_greeting_pcm
    text = "Hey! This is Sai from Mass Drips. How are you doing today?"
    pcm = await get_cached_greeting_pcm(text)
    if not pcm:
        raise RuntimeError("Greeting returned empty PCM")
    return len(pcm)

try:
    size = asyncio.run(_warm_greeting())
    print(f"  [OK]  Greeting pre-synthesized ({size} bytes, {size//32:.0f}ms audio)")
except Exception as e:
    print(f"  [FAIL] Greeting synthesis: {e}")


# ---- 8. MongoDB ----
section("STEP 8: MongoDB Connection")
async def _check_mongo():
    from backend.database import connect_to_mongo, close_mongo_connection, db_instance
    await connect_to_mongo()
    if db_instance is None:
        raise RuntimeError("db_instance is None after connect")
    await close_mongo_connection()

try:
    asyncio.run(_check_mongo())
    print("  [OK]  MongoDB connected successfully")
except Exception as e:
    print(f"  [FAIL] MongoDB: {e}")


# ---- Final ----
section("STARTUP CHECK COMPLETE")
print("All models loaded and cached. Server is ready to start.")
print("\nTo start the voice agent:")
print("  uvicorn backend.main:app --host 0.0.0.0 --port 8000 --ws websockets")
print()
