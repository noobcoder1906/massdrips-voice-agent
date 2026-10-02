"""
backend/voice/tts.py

Zero-latency Text-to-Speech engine using Kokoro ONNX.
Fully offline, zero API cost.

Architecture:
  LLM response text
      │  (per sentence — streaming)
      ▼
  KokoroTTS.synthesize(sentence)
      │  numpy float32 audio @ 24kHz
      ▼
  resample to 16kHz PCM int16
      │  binary bytes
      ▼
  WebSocket binary frame → client

Voice config via .env:
  TTS_VOICE  = af_heart  (default warm female English/Hinglish voice)
  TTS_SPEED  = 1.0       (0.5 – 2.0)
  TTS_SAMPLE_RATE = 24000 (Kokoro native output rate)

Voices available (Kokoro v1):
  English:  af_heart, af_bella, am_adam, bf_emma, bm_george
  Future:   Hindi via espeak-ng backend
"""

import asyncio
import io
import logging
import os
import struct
from typing import AsyncGenerator

import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

TTS_VOICE        = os.getenv("TTS_VOICE", "af_heart")
TTS_SPEED        = float(os.getenv("TTS_SPEED", "1.0"))
KOKORO_SAMPLE_RATE = 24000   # Kokoro native output rate
TARGET_SAMPLE_RATE = 16000   # Must match VAD/STT pipeline


def _resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Simple linear decimation resampler.
    For 24kHz → 16kHz (ratio 2/3), uses scipy if available else numpy interp.
    """
    if orig_sr == target_sr:
        return audio

    try:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(target_sr, orig_sr)
        return resample_poly(audio, target_sr // g, orig_sr // g).astype(np.float32)
    except ImportError:
        # Fallback: linear interpolation (good enough for voice)
        duration = len(audio) / orig_sr
        target_len = int(duration * target_sr)
        x_old = np.linspace(0, 1, len(audio))
        x_new = np.linspace(0, 1, target_len)
        return np.interp(x_new, x_old, audio).astype(np.float32)


def _float32_to_pcm16(audio: np.ndarray) -> bytes:
    """Convert float32 [-1, 1] numpy array to raw 16-bit LE PCM bytes."""
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767).astype(np.int16)
    return pcm.tobytes()


class KokoroTTS:
    """
    Singleton wrapper around kokoro-onnx Kokoro model.
    Lazy initialization — model loads only on first synthesis call.
    """

    _kokoro = None

    @classmethod
    def get_engine(cls):
        if cls._kokoro is None:
            from kokoro_onnx import Kokoro
            logger.info("Loading Kokoro TTS ONNX model...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, "models")
            
            # Check models directory first, then root / cwd
            model_path = os.path.join(models_dir, "kokoro-v1.0.onnx")
            voices_path = os.path.join(models_dir, "voices-v1.0.bin")
            
            if not os.path.exists(model_path):
                model_path = "kokoro-v1.0.onnx"
            if not os.path.exists(voices_path):
                voices_path = "voices-v1.0.bin"
                
            cls._kokoro = Kokoro(model_path, voices_path)
            logger.info("Kokoro TTS loaded successfully.")
        return cls._kokoro

    @classmethod
    def synthesize_to_pcm(cls, text: str, voice: str = TTS_VOICE, speed: float = TTS_SPEED) -> bytes:
        """
        Synthesize text → raw 16kHz 16-bit mono PCM bytes.

        Args:
            text:  Clean, voice-ready text string (single sentence preferred).
            voice: Kokoro voice ID.
            speed: Speech rate multiplier.

        Returns:
            Raw PCM bytes (16kHz, 16-bit, mono) ready for WebSocket delivery.
        """
        if not text.strip():
            return b""

        kokoro = cls.get_engine()

        # Kokoro returns (samples, sample_rate)
        samples, sr = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
        samples = np.array(samples, dtype=np.float32)

        # Resample to 16kHz to match our pipeline
        if sr != TARGET_SAMPLE_RATE:
            samples = _resample(samples, sr, TARGET_SAMPLE_RATE)

        pcm_bytes = _float32_to_pcm16(samples)
        logger.debug(
            f"TTS: '{text[:50]}' → {len(pcm_bytes)} bytes "
            f"({len(pcm_bytes) / (TARGET_SAMPLE_RATE * 2) * 1000:.0f}ms)"
        )
        return pcm_bytes


async def tts_worker(
    response_queue: asyncio.Queue,
    audio_queue: asyncio.Queue,
    tenant_id: str,
    lead_id: str,
) -> None:
    """
    Async worker: consumes LLM response dicts from response_queue,
    synthesizes each sentence, and puts PCM bytes onto audio_queue
    for WebSocket delivery.

    Sentence-level streaming: audio starts playing before the
    full response is synthesized (critical for low latency).

    Args:
        response_queue: Source — receives {"response": str, "user_text": str, ...}
        audio_queue:    Sink   — puts raw PCM bytes (one chunk per sentence)
        tenant_id:      For logging.
        lead_id:        For logging.
    """
    from backend.voice.text_utils import iter_sentences

    logger.info(f"TTS worker started [{tenant_id}/{lead_id}]")
    loop = asyncio.get_event_loop()

    try:
        while True:
            item = await response_queue.get()

            if item is None:
                logger.info(f"TTS worker stopping [{tenant_id}/{lead_id}]")
                response_queue.task_done()
                await audio_queue.put(None)
                break

            response_text = item.get("response", "")
            logger.info(f"TTS synthesizing: '{response_text[:80]}...'")

            sentence_count = 0
            for sentence in iter_sentences(response_text):
                # Run blocking synthesis in thread pool — won't block event loop
                pcm = await loop.run_in_executor(
                    None,
                    KokoroTTS.synthesize_to_pcm,
                    sentence,
                )
                if pcm:
                    await audio_queue.put({
                        "tenant_id": tenant_id,
                        "lead_id":   lead_id,
                        "pcm":       pcm,
                        "text":      sentence,
                    })
                    sentence_count += 1

            logger.info(
                f"TTS [{tenant_id}/{lead_id}]: "
                f"{sentence_count} sentence(s) synthesized"
            )
            response_queue.task_done()

    except asyncio.CancelledError:
        logger.info(f"TTS worker cancelled [{tenant_id}/{lead_id}]")
