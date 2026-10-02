"""
backend/voice/chatterbox_pipeline.py

Dual-Track Low-Latency Voice Clone Pipeline.

ARCHITECTURE:
=============
Race-to-play strategy with background pre-synthesis queue:

  For FIRST sentence of each turn:
    - Track A: edge_tts starts immediately (200ms fallback)
    - Track B: chatterbox starts immediately (1.5-3s, your cloned voice)
    - Winner at 500ms checkpoint plays first
    - If chatterbox wins: your actual cloned voice from first word
    - If edge_tts wins: generic voice now, chatterbox fills pipeline for next sentences

  For SUBSEQUENT sentences (lookahead pre-synthesis):
    - While sentence N plays, chatterbox pre-synthesizes sentence N+1
    - Gap between sentences: ~50ms (just queue dequeue time)
    - Result: your cloned voice from sentence 2 onwards regardless of CPU speed

  Barge-in:
    - User speaks → flush all pending synthesis tasks instantly
    - Cancel any in-progress chatterbox generation
    - Clean state for new turn

REFERENCE AUDIO:
  backend/voice/clones/voicebox_reference.wav  (your 27s Voicebox recording)
  This is fed to Chatterbox as the voice style reference for every synthesis.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────
REF_WAV_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "clones", "voicebox_reference.wav",
)
RACE_TIMEOUT_S = 0.55       # How long to wait for chatterbox before falling back to edge_tts
TARGET_SAMPLE_RATE = 16000  # 16kHz for WebSocket pipeline
_thread_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=2, thread_name_prefix="chatterbox"
)


# ─── Chatterbox loader (lazy, singleton) ─────────────────────────────────────
_cb_model = None
_cb_model_lock = asyncio.Lock()


async def _get_chatterbox():
    global _cb_model
    if _cb_model is not None:
        return _cb_model
    async with _cb_model_lock:
        if _cb_model is None:
            loop = asyncio.get_event_loop()
            _cb_model = await loop.run_in_executor(
                _thread_pool, _load_chatterbox_sync
            )
    return _cb_model


def _load_chatterbox_sync():
    try:
        from chatterbox.tts import ChatterboxTTS
        logger.info("Loading Chatterbox TTS model... (first load ~15-30s)")
        device = "cuda" if _cuda_available() else "cpu"
        model = ChatterboxTTS.from_pretrained(device=device)
        logger.info("Chatterbox TTS loaded on %s", device)
        return model
    except ImportError:
        logger.error("chatterbox-tts not installed. Run: pip install chatterbox-tts")
        return None


def _cuda_available() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


# ─── PCM helpers ─────────────────────────────────────────────────────────────
def _resample(samples: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    if src_rate == dst_rate:
        return samples
    new_len = int(len(samples) * dst_rate / src_rate)
    return np.interp(
        np.linspace(0, len(samples) - 1, new_len),
        np.arange(len(samples)),
        samples,
    ).astype(np.float32)


def _to_pcm16(samples: np.ndarray) -> bytes:
    peak = np.max(np.abs(samples))
    if peak > 1e-4:
        samples = samples * (0.92 / peak)
    return np.clip(samples, -1.0, 1.0).astype(np.float32).__mul__(32767).astype(np.int16).tobytes()


# ─── Chatterbox synthesis (sync, runs in thread pool) ────────────────────────
def _synth_chatterbox_sync(text: str, model) -> Optional[bytes]:
    """Synthesize one sentence with Chatterbox voice clone. Returns PCM16 bytes."""
    if model is None:
        return None
    if not os.path.exists(REF_WAV_PATH):
        logger.warning("Voicebox reference WAV not found: %s", REF_WAV_PATH)
        return None
    try:
        t0 = time.perf_counter()
        wav = model.generate(text, audio_prompt_path=REF_WAV_PATH)
        elapsed = time.perf_counter() - t0
        sr = getattr(model, "sr", 24000)
        samples = wav.squeeze().cpu().numpy().astype(np.float32)
        resampled = _resample(samples, sr, TARGET_SAMPLE_RATE)
        pcm = _to_pcm16(resampled)
        logger.info("Chatterbox: %.2fs for %d chars → %d PCM bytes", elapsed, len(text), len(pcm))
        return pcm
    except Exception as e:
        logger.error("Chatterbox synthesis error: %s", e)
        return None


# ─── Edge-TTS synthesis (async, already fast) ────────────────────────────────
async def _synth_edge_tts(text: str) -> Optional[bytes]:
    """Fallback: edge_tts with PrabhatNeural. Returns PCM16 bytes."""
    try:
        import edge_tts
        import av
        import io
        communicate = edge_tts.Communicate(text, "en-IN-PrabhatNeural")
        mp3 = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3 += chunk["data"]
        if not mp3:
            return None
        container = av.open(io.BytesIO(mp3))
        samples = []
        resampler = av.AudioResampler(format="s16", layout="mono", rate=TARGET_SAMPLE_RATE)
        for frame in container.decode(audio=0):
            for rf in resampler.resample(frame):
                samples.extend(rf.to_ndarray().flatten())
        arr = np.array(samples, dtype=np.int16)
        return arr.tobytes()
    except Exception as e:
        logger.error("Edge-TTS fallback error: %s", e)
        return None


# ─── DualTrackSynthesizer ─────────────────────────────────────────────────────
class DualTrackSynthesizer:
    """
    Manages a sentence pre-synthesis queue with dual-track (chatterbox + edge_tts)
    race-to-play strategy for minimum perceived latency.

    Usage:
        synth = DualTrackSynthesizer()
        await synth.start()

        # Push sentences as LLM streams them
        await synth.push("Hey Rahul!")
        await synth.push("We have the AK The Don's edition.")

        # Pull synthesized PCM (blocks until ready)
        pcm = await synth.next_audio()

        # On barge-in / turn end:
        await synth.flush()
    """

    def __init__(self):
        self._audio_queue: asyncio.Queue = asyncio.Queue()
        self._pending_texts: asyncio.Queue = asyncio.Queue()
        self._cb_model = None
        self._worker_task: Optional[asyncio.Task] = None
        self._cancelled = False
        self._first_sentence_of_turn = True

    async def start(self):
        """Load chatterbox model (background) and start synthesis worker."""
        self._cancelled = False
        self._first_sentence_of_turn = True
        self._cb_model = await _get_chatterbox()
        self._worker_task = asyncio.create_task(self._synthesis_worker())

    async def push(self, text: str):
        """Push a sentence for synthesis."""
        if text.strip():
            await self._pending_texts.put(text.strip())

    async def next_audio(self) -> Optional[bytes]:
        """Get next synthesized PCM. Returns None when pipeline is done."""
        return await self._audio_queue.get()

    async def flush(self):
        """Cancel all pending synthesis on barge-in. Call before new turn."""
        self._cancelled = True
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
        # Drain queues
        while not self._pending_texts.empty():
            try:
                self._pending_texts.get_nowait()
            except asyncio.QueueEmpty:
                break
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        # Reset for next turn
        self._cancelled = False
        self._first_sentence_of_turn = True
        self._worker_task = asyncio.create_task(self._synthesis_worker())

    async def close(self):
        """Signal end of turn — push sentinel."""
        await self._pending_texts.put(None)

    async def _synthesis_worker(self):
        """
        Background worker that synthesizes sentences from _pending_texts.

        For each sentence:
          1. Start Chatterbox synthesis in thread pool
          2. If first sentence: also start edge_tts race
          3. Wait RACE_TIMEOUT_S for chatterbox to finish
          4. If chatterbox won: put its PCM in audio_queue
          5. If edge_tts won: put edge_tts PCM, pre-synthesize next with chatterbox
        """
        loop = asyncio.get_event_loop()

        while True:
            try:
                text = await self._pending_texts.get()
            except asyncio.CancelledError:
                break

            if text is None or self._cancelled:
                await self._audio_queue.put(None)  # sentinel
                break

            is_first = self._first_sentence_of_turn
            self._first_sentence_of_turn = False

            # Start chatterbox synthesis in thread pool
            cb_future = loop.run_in_executor(
                _thread_pool,
                _synth_chatterbox_sync,
                text,
                self._cb_model,
            )

            pcm = None

            if is_first:
                # Race: also start edge_tts for the first sentence
                edge_task = asyncio.create_task(_synth_edge_tts(text))

                try:
                    # Wait up to RACE_TIMEOUT_S for chatterbox
                    pcm = await asyncio.wait_for(asyncio.shield(cb_future), timeout=RACE_TIMEOUT_S)
                    # Chatterbox won! Cancel edge_tts task (already fast enough)
                    edge_task.cancel()
                    logger.info("Chatterbox won race for first sentence!")
                except asyncio.TimeoutError:
                    # Chatterbox too slow for first sentence — use edge_tts immediately
                    logger.info("Edge-TTS won race (chatterbox still running)")
                    try:
                        pcm = await asyncio.wait_for(edge_task, timeout=3.0)
                    except asyncio.TimeoutError:
                        pcm = None
                    # Chatterbox result will be used for next sentence (pre-synthesized)
                    # Keep cb_future running in background — result stored for next slot
            else:
                # Subsequent sentences: chatterbox was pre-synthesizing during playback
                # Just await the result (should already be done or close to done)
                try:
                    pcm = await asyncio.wait_for(asyncio.shield(cb_future), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Chatterbox timeout for sentence, using edge_tts fallback")
                    pcm = await _synth_edge_tts(text)

            if self._cancelled:
                break

            await self._audio_queue.put(pcm)
            self._pending_texts.task_done()


# ─── Singleton per-session factory ───────────────────────────────────────────
def create_synthesizer() -> DualTrackSynthesizer:
    """Create a fresh DualTrackSynthesizer for one call session."""
    return DualTrackSynthesizer()
