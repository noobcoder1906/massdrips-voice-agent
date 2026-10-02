"""
backend/voice/vad.py

Silero VAD (Voice Activity Detection) using ONNX Runtime.
Processes raw PCM 16-bit mono 16kHz audio chunks and detects
speech frames vs silence frames with natural conversational thresholds
and instant barge-in detection.
"""
import asyncio
import logging
import urllib.request
from pathlib import Path

import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

# Constants
SAMPLE_RATE = 16000          # 16kHz
FRAME_DURATION_MS = 30       # 30ms frames
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
FRAME_BYTES = FRAME_SAMPLES * 2  # 960 bytes per int16 sample
SPEECH_THRESHOLD = 0.5       # Silero confidence threshold
MIN_SPEECH_FRAMES = 4        # 120ms of speech triggers barge-in / speech start
SILENCE_FRAMES_TO_END = 25   # 25 frames * 30ms = 750ms natural conversational pause

# Silero VAD ONNX model URL
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
        return float(out.squeeze())

    def reset(self) -> None:
        self._reset_state()


class VoiceActivityDetector:
    """
    High-level VAD manager for one WebSocket session.
    Supports speech boundary detection, utterance accumulation, and barge-in callback.
    """

    def __init__(self, output_queue: asyncio.Queue, on_speech_start=None):
        self._vad = SileroVAD()
        self._out_q = output_queue
        self._on_speech_start = on_speech_start
        self._buffer = b""         # rolling byte buffer
        self._speech_buf = b""     # accumulates current utterance
        self._speech_count = 0     # consecutive speech frames
        self._silence_count = 0    # consecutive silence frames after speech

    async def feed(self, data: bytes) -> None:
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

            # Instant Barge-In detection when user starts speaking
            if self._speech_count == MIN_SPEECH_FRAMES and self._on_speech_start:
                try:
                    res = self._on_speech_start()
                    if asyncio.iscoroutine(res):
                        asyncio.create_task(res)
                except Exception as e:
                    logger.debug("on_speech_start callback error: %s", e)
        else:
            if self._speech_count >= MIN_SPEECH_FRAMES:
                # User was speaking, now in pause
                self._silence_count += 1
                self._speech_buf += frame
                # End of turn detected after 750ms natural pause
                if self._silence_count >= SILENCE_FRAMES_TO_END:
                    await self._emit_utterance()
            else:
                self._speech_count = 0
                self._speech_buf = b""

    async def _emit_utterance(self) -> None:
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
        if self._speech_count >= MIN_SPEECH_FRAMES and self._speech_buf:
            await self._emit_utterance()
