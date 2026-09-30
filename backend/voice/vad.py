"""
backend/voice/vad.py

Silero VAD (Voice Activity Detection) using ONNX Runtime.
Processes raw PCM 16-bit mono 16kHz audio chunks and detects
speech frames vs silence frames.

Architecture:
  WebSocket binary chunk --> VAD --> speech frames --> STT Queue
"""
import asyncio
import logging
import struct
import urllib.request
from pathlib import Path

import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # 16kHz — Whisper's native rate
FRAME_DURATION_MS = 30       # 30ms frames
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
FRAME_BYTES = FRAME_SAMPLES * 2  # 2 bytes per int16 sample
SPEECH_THRESHOLD = 0.5       # Silero confidence threshold
MIN_SPEECH_FRAMES = 3        # Min consecutive speech frames before triggering
SILENCE_FRAMES_TO_END = 20   # 600ms silence ends an utterance

# Silero VAD ONNX model URL (pinned version)
SILERO_MODEL_URL = (
    "https://github.com/snakers4/silero-vad/raw/v4.0stable/"
    "files/silero_vad.onnx"
)
MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "silero_vad.onnx"


def _download_model_if_needed() -> None:
    """Download the Silero VAD ONNX model if not present locally."""
    if MODEL_PATH.exists():
        return
    logger.info("Downloading Silero VAD ONNX model (~2MB)...")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(SILERO_MODEL_URL, MODEL_PATH)
    logger.info(f"Silero VAD model saved to {MODEL_PATH}")


class SileroVAD:
    """
    Wraps the Silero VAD ONNX model for per-call voice activity detection.

    Each active WebSocket call should create its own SileroVAD instance
    to maintain per-session LSTM state (h, c tensors).
    """

    def __init__(self):
        _download_model_if_needed()
        opts = ort.SessionOptions()
        opts.log_severity_level = 3  # Suppress INFO/WARNING noise
        self._session = ort.InferenceSession(
            str(MODEL_PATH),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset LSTM hidden state for new call / new utterance."""
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self._sample_rate_tensor = np.array(SAMPLE_RATE, dtype=np.int64)

    def _predict_frame(self, pcm_frame: bytes) -> float:
        """
        Run one 30ms PCM frame through Silero VAD.

        Args:
            pcm_frame: Exactly FRAME_BYTES of raw 16-bit LE PCM audio.

        Returns:
            Speech probability (0.0 – 1.0).
        """
        # Convert bytes → float32 in [-1, 1]
        samples = np.frombuffer(pcm_frame, dtype=np.int16).astype(np.float32)
        samples /= 32768.0
        audio_tensor = samples.reshape(1, -1)  # [1, 480]

        inputs = {
            "input":       audio_tensor,
            "h":           self._h,
            "c":           self._c,
            "sr":          self._sample_rate_tensor,
        }
        out, h_out, c_out = self._session.run(
            ["output", "hn", "cn"], inputs
        )
        self._h = h_out
        self._c = c_out
        return float(out[0])

    def reset(self) -> None:
        """Public method to reset state between utterances."""
        self._reset_state()


class VoiceActivityDetector:
    """
    High-level VAD manager for one WebSocket session.

    Buffers incoming binary audio, splits into 30ms frames,
    runs Silero, and emits complete utterance byte-strings
    onto the provided asyncio output queue.

    Usage:
        detector = VoiceActivityDetector(stt_queue)
        await detector.feed(raw_bytes)   # call on every WS binary message
        await detector.flush()           # call on WS disconnect
    """

    def __init__(self, output_queue: asyncio.Queue):
        self._vad = SileroVAD()
        self._out_q = output_queue
        self._buffer = b""         # rolling byte buffer
        self._speech_buf = b""     # accumulates current utterance
        self._speech_count = 0     # consecutive speech frames
        self._silence_count = 0    # consecutive silence frames after speech

    async def feed(self, data: bytes) -> None:
        """
        Accept raw binary audio bytes from the WebSocket.
        Data may be any length; internally sliced into 30ms frames.
        """
        self._buffer += data
        while len(self._buffer) >= FRAME_BYTES:
            frame, self._buffer = (
                self._buffer[:FRAME_BYTES],
                self._buffer[FRAME_BYTES:],
            )
            await self._process_frame(frame)

    async def _process_frame(self, frame: bytes) -> None:
        prob = self._vad._predict_frame(frame)
        is_speech = prob >= SPEECH_THRESHOLD

        if is_speech:
            self._speech_count += 1
            self._silence_count = 0
            self._speech_buf += frame
        else:
            if self._speech_count >= MIN_SPEECH_FRAMES:
                # We were in speech, now silence
                self._silence_count += 1
                self._speech_buf += frame  # include trailing silence
                if self._silence_count >= SILENCE_FRAMES_TO_END:
                    await self._emit_utterance()
            else:
                # Too short to count — discard
                self._speech_count = 0
                self._speech_buf = b""

    async def _emit_utterance(self) -> None:
        """Push collected speech bytes onto the STT queue."""
        if self._speech_buf:
            logger.info(
                f"VAD: utterance detected, "
                f"{len(self._speech_buf) / FRAME_BYTES * FRAME_DURATION_MS:.0f}ms"
            )
            await self._out_q.put(self._speech_buf)
        self._speech_buf = b""
        self._speech_count = 0
        self._silence_count = 0
        self._vad.reset()

    async def flush(self) -> None:
        """Flush any remaining buffered speech at end of call."""
        if self._speech_count >= MIN_SPEECH_FRAMES and self._speech_buf:
            await self._emit_utterance()
