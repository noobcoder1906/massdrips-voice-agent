"""
backend/voice/stt.py

Local Speech-to-Text using faster-whisper (CTranslate2).
Zero API cost, runs fully on-device (CPU or CUDA).

Model selection via environment:
  WHISPER_MODEL  = "tiny" | "base" | "small" | "medium" | "large-v3"
  WHISPER_DEVICE = "cpu" | "cuda"
  WHISPER_LANG   = "hi" | "en" | None (auto-detect)

Architecture:
  VAD output queue --> STT worker --> transcript string --> response queue
"""

import asyncio
import io
import logging
import os
import struct
import tempfile
import wave
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_LANG   = os.getenv("WHISPER_LANG", None)  # None = auto-detect
SAMPLE_RATE    = 16000   # Must match VAD


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Convert raw 16-bit LE PCM bytes to a WAV byte buffer."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)         # Mono
        wf.setsampwidth(2)         # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


class WhisperSTT:
    """
    Singleton-ish wrapper around faster-whisper.WhisperModel.

    Lazy initialization so the model only loads when first used,
    keeping startup time fast.
    """

    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from faster_whisper import WhisperModel
            logger.info(
                f"Loading Whisper model '{WHISPER_MODEL}' "
                f"on {WHISPER_DEVICE}..."
            )
            cls._model = WhisperModel(
                WHISPER_MODEL,
                device=WHISPER_DEVICE,
                compute_type="int8",   # INT8 quantized — fastest on CPU
            )
            logger.info("Whisper model loaded successfully.")
        return cls._model

    @classmethod
    def transcribe(cls, pcm_bytes: bytes) -> str:
        """
        Transcribe raw PCM bytes to text.

        Args:
            pcm_bytes: Raw 16-bit LE mono 16kHz PCM audio.

        Returns:
            Transcribed text string (stripped), or empty string.
        """
        model = cls.get_model()

        # Convert PCM → float32 numpy array
        samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        samples /= 32768.0  # Normalize to [-1.0, 1.0]

        kwargs = dict(
            beam_size=3,
            language=WHISPER_LANG,
            condition_on_previous_text=False,
            vad_filter=False,  # We already did VAD — no double filtering
        )
        segments, info = model.transcribe(samples, **kwargs)

        text = " ".join(seg.text.strip() for seg in segments).strip()

        if text:
            lang = info.language
            prob = info.language_probability
            logger.info(f"STT [{lang} {prob:.0%}]: '{text}'")
        else:
            logger.debug("STT: silence / no speech detected")

        return text


async def stt_worker(
    stt_queue: asyncio.Queue,
    transcript_queue: asyncio.Queue,
    tenant_id: str,
    lead_id: str,
) -> None:
    """
    Async worker: consumes utterance PCM blobs from stt_queue,
    transcribes them, and puts results on transcript_queue.

    Designed to run as an asyncio.Task per WebSocket session.

    Args:
        stt_queue:        Source queue — receives raw PCM bytes (one utterance each).
        transcript_queue: Sink queue   — puts transcribed text strings.
        tenant_id:        For logging/context.
        lead_id:          For logging/context.
    """
    logger.info(f"STT worker started [{tenant_id}/{lead_id}]")
    loop = asyncio.get_event_loop()

    try:
        while True:
            pcm_bytes: bytes = await stt_queue.get()

            if pcm_bytes is None:
                # Sentinel: shut down the worker
                logger.info(f"STT worker stopping [{tenant_id}/{lead_id}]")
                stt_queue.task_done()
                break

            # Run blocking Whisper in a thread to not block the event loop
            text = await loop.run_in_executor(
                None, WhisperSTT.transcribe, pcm_bytes
            )

            if text:
                await transcript_queue.put({
                    "tenant_id":  tenant_id,
                    "lead_id":    lead_id,
                    "transcript": text,
                })

            stt_queue.task_done()

    except asyncio.CancelledError:
        logger.info(f"STT worker cancelled [{tenant_id}/{lead_id}]")
