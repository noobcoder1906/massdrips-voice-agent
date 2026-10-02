from dotenv import load_dotenv
load_dotenv()
"""
backend/voice/stt.py

Speech-to-Text with multi-engine support:
  1. Groq Cloud Whisper (whisper-large-v3-turbo) -- ultra-low latency (~150ms)
  2. Local faster-whisper fallback -- zero API cost, runs on CPU/CUDA

Architecture:
  VAD output queue --> STT worker --> transcript string --> response queue
"""

import asyncio
import io
import json
import logging
import os
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
    STT Engine wrapper with Groq Cloud priority and local faster-whisper fallback.
    """

    _model = None

    @classmethod
    def get_local_model(cls):
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
        Prioritizes Groq Whisper (150ms) -> falls back to local Faster-Whisper.
        """
        groq_api_key = os.getenv("GROQ_API_KEY", "")
        if groq_api_key:
            try:
                from groq import Groq
                wav_bytes = _pcm_to_wav(pcm_bytes)
                client = Groq(api_key=groq_api_key)
                res = client.audio.transcriptions.create(
                    file=("audio.wav", wav_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="text",
                    prompt="Mass Drips, streetwear, tees, oversized tees, hoodies, Kollywood, Bollywood, Tollywood, 240 GSM, 380 GSM, Jana Nayagan, Kismat, DRIP10, Rahul",
                )
                text = res.strip() if isinstance(res, str) else getattr(res, "text", "").strip()
                if text:
                    logger.info(f"Groq STT: '{text}'")
                    return text
            except Exception as e:
                logger.warning(f"Groq STT failed ({e}), attempting local fallback...")

        try:
            model = cls.get_local_model()
            samples = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
            samples /= 32768.0

            kwargs = dict(
                beam_size=3,
                language=WHISPER_LANG,
                condition_on_previous_text=False,
                vad_filter=False,
                initial_prompt="Mass Drips, streetwear, tees, oversized tees, hoodies, Kollywood, Bollywood, Tollywood, 240 GSM, 380 GSM, Jana Nayagan, Kismat, DRIP10, Rahul",
            )
            segments, info = model.transcribe(samples, **kwargs)
            text = " ".join(seg.text.strip() for seg in segments).strip()

            if text:
                logger.info(f"Local STT: '{text}'")
            return text
        except Exception as e:
            logger.error(f"Local STT error: {e}")
            return ""


async def stt_worker(
    stt_queue: asyncio.Queue,
    transcript_queue: asyncio.Queue,
    tenant_id: str,
    lead_id: str,
    websocket = None,
    call_transcript: list = None,
) -> None:
    """
    Async worker: consumes utterance PCM blobs from stt_queue,
    transcribes them, and puts results on transcript_queue.
    Relays transcript to frontend WebSocket and call transcript log.
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

            # Run STT in thread pool
            text = await loop.run_in_executor(
                None, WhisperSTT.transcribe, pcm_bytes
            )

            if text:
                if call_transcript is not None:
                    call_transcript.append({"role": "user", "text": text})

                if websocket:
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "text": text,
                        }))
                    except Exception:
                        pass

                await transcript_queue.put({
                    "tenant_id":  tenant_id,
                    "lead_id":    lead_id,
                    "transcript": text,
                })

            stt_queue.task_done()

    except asyncio.CancelledError:
        logger.info(f"STT worker cancelled [{tenant_id}/{lead_id}]")
