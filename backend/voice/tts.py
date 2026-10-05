"""
backend/voice/tts.py

Text-to-Speech module for VoxSales voice agent.

ARCHITECTURE OVERVIEW (for future agents):
==========================================
This module handles all TTS synthesis for the voice pipeline.

Pipeline position:
  LLM response_queue --> tts_worker() --> audio_queue --> WebSocket

THREE synthesis modes (configured via TTS_PROVIDER in .env):
  1. edge_tts  : Microsoft Edge TTS (free, online, ~200ms RTT, no cloning)
  2. kokoro    : Local Kokoro-ONNX (offline, ~150ms on CPU, voice-clonable)
  3. kokoro_clone: Kokoro with custom .npy voice style embedding (cloned voice)

VOICE CLONING STATUS & HOW IT WORKS:
=====================================
Kokoro-ONNX supports voice cloning via a "voice style embedding" -- a numpy
array of shape (1, N, 256) representing vocal characteristics extracted from a
reference audio file.

HOW TO GENERATE A CLONE:
  1. Record a clean 30-60 second WAV file (16kHz mono, no noise).
  2. Run the helper script:
       python backend/scripts/generate_voice_clone.py --input backend/voice/clones/my_voice.wav
  3. The script creates:
       backend/voice/clones/my_voice_style.npy   <-- this file enables cloning
  4. Set TTS_PROVIDER=kokoro_clone in .env

CURRENT STATUS (2026-10-02):
  - WAV files exist in backend/voice/clones/ (test_founder_voice.wav, etc.)
  - my_voice_style.npy does NOT exist yet (clone not generated)
  - TTS_PROVIDER=edge_tts is active (fallback to Microsoft neural voice)
  - Edge-TTS sounds robotic because it's a generic Microsoft voice, not cloned

FEASIBILITY:
  - True voice cloning with Kokoro: FEASIBLE but LIMITED
    * Kokoro uses a fixed phoneme-to-style mapping, not a free-form encoder
    * It can adopt SOME vocal texture from the reference but not full identity
    * For truly identical voice cloning: use ElevenLabs API (cost ~$0.18/1k chars)
  - Edge-TTS (current): Free, online, natural but NOT the founder's voice
  - Kokoro local: Free, offline, ~150-300ms latency on CPU; needs .npy generation

EFFICIENCY:
  - Edge-TTS: ~150-250ms per sentence, requires internet
  - Kokoro CPU: ~200-400ms per sentence (depends on text length)
  - Kokoro CUDA: ~50-100ms per sentence (if GPU available)
  - Sentence-level streaming in tts_worker() means first audio plays in <500ms
    total even if full response takes longer -- critical for phone UX

LATENCY OPTIMIZATION:
  - tts_worker() splits response into sentences and synthesizes + streams each
    sentence independently so audio starts playing before full response is done.
  - The LLM (Groq) streams tokens -- first sentence available in ~100ms.
  - Combined pipeline target: <600ms voice-to-voice latency (Speech --> Audio out)
"""

import asyncio
import io
import logging
import os

import numpy as np
import soundfile as sf

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ Config ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬ÃƒÂ¢Ã¢â‚¬ÂÃ¢â€šÂ¬
TTS_PROVIDER    = os.getenv("TTS_PROVIDER", "edge_tts").lower()  # edge_tts | kokoro | kokoro_clone
TTS_VOICE       = os.getenv("TTS_VOICE", "en-IN-PrabhatNeural")  # Edge-TTS voice
TTS_SPEED       = float(os.getenv("TTS_SPEED", "1.08"))           # Slightly fast for phone calls
TARGET_SAMPLE_RATE = 16000   # 16kHz -- matches STT pipeline + WebSocket expectation
AUDIO_CHUNK_SIZE = 640        # 20ms of 16kHz 16-bit mono audio per chunk


def _resample(samples: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """
    Naive linear interpolation resampler (good enough for speech, no scipy dep).
    For production use librosa.resample or scipy.signal.resample for higher quality.
    """
    if src_rate == dst_rate:
        return samples
    ratio = dst_rate / src_rate
    new_len = int(len(samples) * ratio)
    return np.interp(
        np.linspace(0, len(samples) - 1, new_len),
        np.arange(len(samples)),
        samples,
    ).astype(np.float32)


def _float32_to_pcm16(samples: np.ndarray, target_peak: float = 0.95) -> bytes:
    """Normalize and convert float32 [-1, 1] samples to 16-bit signed PCM bytes with volume boost."""
    if len(samples) == 0:
        return b""
    max_amp = np.max(np.abs(samples))
    if max_amp > 1e-4:
        samples = samples * (target_peak / max_amp)
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767).astype(np.int16).tobytes()


class KokoroTTS:
    """
    Singleton wrapper around kokoro-onnx Kokoro model.

    Lazy initialization -- model loads only on first synthesis call.
    Kokoro is a local ONNX TTS model with built-in voices and optional
    style-based voice cloning via .npy embedding files.

    Supported voices (built-in, no cloning needed):
      - af_heart  : American female, warm
      - hm_omega  : American male, deep
      - af_sky    : American female, clear
      - am_adam   : American male, neutral

    Voice cloning requires a pre-generated .npy style embedding file.
    See module docstring above for how to generate one.
    """

    _kokoro = None

    @classmethod
    def get_engine(cls):
        """Lazily initialize the Kokoro ONNX engine (thread-safe via GIL)."""
        if cls._kokoro is None:
            from kokoro_onnx import Kokoro
            logger.info("Loading Kokoro TTS ONNX model...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(base_dir, "models")

            # Check models/ directory first, then fall back to CWD
            model_path  = os.path.join(models_dir, "kokoro-v1.0.onnx")
            voices_path = os.path.join(models_dir, "voices-v1.0.bin")

            if not os.path.exists(model_path):
                model_path = "kokoro-v1.0.onnx"
            if not os.path.exists(voices_path):
                voices_path = "voices-v1.0.bin"

            cls._kokoro = Kokoro(model_path, voices_path)
            logger.info("Kokoro TTS loaded successfully.")
        return cls._kokoro

    @classmethod
    def _load_voice_style(cls) -> np.ndarray | None:
        """
        Load a pre-generated voice style embedding (.npy) for voice cloning.

        The .npy file is generated by backend/scripts/generate_voice_clone.py
        from a reference WAV recording. Shape must be (1, N, 256).

        Returns:
            numpy array if the clone file exists and is valid, else None.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        clone_path = os.path.join(base_dir, "clones", "my_voice_style.npy")

        if not os.path.exists(clone_path):
            logger.debug(
                "Voice clone file not found at %s. "
                "Run backend/scripts/generate_voice_clone.py to create it.",
                clone_path,
            )
            return None

        try:
            style = np.load(clone_path)
            # Kokoro expects voice style shape: (T, 1, 256) -- T phoneme frames, 1 batch, 256 features.
            # This matches the output of kokoro.get_voice_style(name).
            # OLD bad format was (1, T, 256) -- batch-first -- reject that.
            if style.ndim == 3 and style.shape[0] == 1 and style.shape[2] == 256 and style.shape[1] > 10:
                logger.warning(
                    "Voice clone .npy has old format (1, T, 256) = %s -- "
                    "please regenerate: python backend/scripts/generate_voice_clone.py "
                    "Falling back to built-in voice.",
                    style.shape,
                )
                return None
            # Validate correct Kokoro format: (T, 1, 256)
            if style.ndim == 3 and style.shape[1] == 1 and style.shape[2] == 256:
                pass  # correct format -- proceed
            logger.info(
                "Loaded custom voice style embedding: shape=%s, path=%s",
                style.shape, clone_path
            )
            return style
        except Exception as e:
            logger.warning("Failed to load voice style embedding: %s", e)
            return None

    @classmethod
    def _resolve_voice(cls, voice: str):
        """
        Resolve a voice identifier to either:
          - a Kokoro built-in voice string (e.g. "af_heart"), or
          - a numpy style embedding array (for cloned voices)

        Priority:
          1. If TTS_PROVIDER == "kokoro_clone" and .npy exists --> use clone
          2. If voice param is "my_voice"/"clone"/"custom"     --> try clone
          3. Otherwise                                          --> use built-in voice string
        """
        if TTS_PROVIDER == "kokoro_clone" or voice in ("my_voice", "clone", "custom"):
            style = cls._load_voice_style()
            if style is not None:
                return style  # numpy array passed directly to kokoro.create()
            else:
                logger.warning(
                    "Clone voice requested but my_voice_style.npy not found. "
                    "Falling back to built-in voice: af_heart"
                )
                return "af_heart"

        # Default: use voice string if valid Kokoro voice, else fallback to af_heart
        if isinstance(voice, str) and (voice.startswith('en-') or voice.startswith('hi-') or 'Neural' in voice):
            return 'af_heart'
        return voice

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """
        Pre-process text for natural TTS pronunciation.

        Handles:
        - Rupee symbol --> spoken "rupees"
        - Markdown artifacts (*, #, _, `) stripped
        - Price formatting: "1,499" --> "1499" (commas cause pause in TTS)
        - Trailing whitespace
        """
        t = (text
             .replace("ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¹", " rupees ")
             .replace("Rs.", " rupees ")
             .replace("Rs ", " rupees "))
        # Remove markdown characters that TTS reads aloud
        for ch in ("*", "#", "_", "`", "~"):
            t = t.replace(ch, "")
        # Remove digit-comma that causes weird pauses (e.g. "1,499" -> "1499")
        import re
        t = re.sub(r"(\d),(\d{3})", r"\1\2", t)
        return t.strip()

    @classmethod
    def synthesize_to_pcm(cls, text: str, voice: str = TTS_VOICE, speed: float = TTS_SPEED) -> bytes:
        """
        Synthesize text to raw 16kHz 16-bit mono PCM bytes via Kokoro ONNX.

        This is the hot path for the real-time voice pipeline. Called per-sentence
        from tts_worker() so audio streams incrementally.

        Args:
            text:  Clean spoken sentence (one sentence preferred for low latency).
            voice: Kokoro built-in voice ID or clone identifier.
            speed: Speech rate (1.0 = normal, 1.1 = 10% faster).

        Returns:
            Raw PCM bytes ready for WebSocket binary delivery.
            Returns b"" if input is empty or synthesis fails.

        Performance:
            ~150-300ms on CPU, ~50-100ms on CUDA. Sentence-level streaming
            means first audio reaches client before full response is synthesized.
        """
        clean = cls._clean_text(text)
        if not clean:
            return b""

        kokoro = cls.get_engine()
        resolved_voice = cls._resolve_voice(voice)

        try:
            # kokoro.create() returns (samples: np.ndarray, sample_rate: int)
            samples, sr = kokoro.create(clean, voice=resolved_voice, speed=speed, lang="en-us")
            samples = np.array(samples, dtype=np.float32)

            # Resample to 16kHz to match STT pipeline
            if sr != TARGET_SAMPLE_RATE:
                samples = _resample(samples, sr, TARGET_SAMPLE_RATE)

            pcm_bytes = _float32_to_pcm16(samples)
            logger.debug(
                "TTS: '%s' --> %d bytes (%.0fms audio)",
                text[:50], len(pcm_bytes),
                len(pcm_bytes) / (TARGET_SAMPLE_RATE * 2) * 1000,
            )
            return pcm_bytes

        except Exception as e:
            logger.error("Kokoro synthesis failed for '%s': %s", text[:50], e)
            return b""

    @classmethod
    def synthesize_to_wav(cls, text: str, voice: str = "af_heart", speed: float = TTS_SPEED) -> bytes:
        """
        Synthesize text to WAV bytes (for file download / testing endpoints).

        Uses Kokoro built-in voice by default (not clone) for stable output.
        Clone voice via TTS_PROVIDER=kokoro_clone or voice="my_voice".

        Returns WAV bytes (44-byte header + PCM data), or b"" on failure.
        """
        clean = cls._clean_text(text)
        if not clean:
            return b""

        try:
            kokoro = cls.get_engine()
            resolved_voice = cls._resolve_voice(voice)
            samples, sr = kokoro.create(clean, voice=resolved_voice, speed=speed, lang="en-us")
            samples = np.array(samples, dtype=np.float32)

            buf = io.BytesIO()
            sf.write(buf, samples, sr, format="WAV")
            return buf.getvalue()
        except Exception as e:
            logger.error("Kokoro WAV synthesis failed: %s", e)
            return b""

    @classmethod
    async def synthesize_with_edge_tts(
        cls,
        text: str,
        voice: str = TTS_VOICE,
        speed: float = TTS_SPEED,
    ) -> bytes:
        """
        Synthesize speech using Microsoft Edge TTS (free, online).

        IMPORTANT: Edge-TTS does NOT support voice cloning. It uses Microsoft's
        neural voices. The "en-IN-NeerjaExpressiveNeural" voice sounds like a
        natural Indian English female speaker but is NOT the founder's voice.

        To use voice cloning, switch to TTS_PROVIDER=kokoro_clone in .env
        after generating the .npy style file.

        Args:
            voice: Edge-TTS voice name (see https://bit.ly/edge-tts-voices)
            speed: Multiplier (converted to Edge-TTS rate string, e.g. "+8%")

        Returns:
            MP3 audio bytes, or b"" on failure.

        Latency:
            ~150-250ms including network RTT (requires internet).
            Much faster than Kokoro on CPU for short sentences.
        """
        clean = cls._clean_text(text)
        if not clean:
            return b""

        try:
            import edge_tts
            # Convert float speed to Edge-TTS rate string: 1.08 -> "+8%", 0.95 -> "-5%"
            rate_pct = int((speed - 1.0) * 100)
            rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

            communicate = edge_tts.Communicate(clean, voice, rate=rate_str)
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])

            if audio_data:
                return bytes(audio_data)
            logger.warning("Edge-TTS returned empty audio for: '%s'", text[:50])
            return b""

        except Exception as e:
            logger.warning("Edge-TTS failed (%s) for '%s'", e, text[:50])
            return b""


    @classmethod
    async def synthesize_with_elevenlabs(
        cls,
        text: str,
        voice_id: str,
    ) -> bytes:
        import os
        import httpx
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not found in .env")
            return b""
            
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",  # Fastest model for real-time
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=10.0)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                    return b""
        except Exception as e:
            logger.warning(f"ElevenLabs synthesis failed: {e}")
            return b""

    @classmethod
    async def synthesize_to_pcm_async(
        cls,
        text: str,
        voice: str = TTS_VOICE,
        speed: float = TTS_SPEED,
    ) -> bytes:
        """
        Unified async TTS entry point. Routes to the correct provider based on
        TTS_PROVIDER env variable.

        Returns raw 16kHz 16-bit mono PCM bytes in all cases (converts from
        MP3/WAV as needed so callers don't need to care about format).

        Provider routing:
          edge_tts       --> synthesize_with_edge_tts() + MP3-to-PCM conversion
          kokoro         --> synthesize_to_pcm() via thread pool (non-blocking)
          kokoro_clone   --> synthesize_to_pcm() with clone style via thread pool
        """
        clean = cls._clean_text(text)
        if not clean:
            return b""

        loop = asyncio.get_event_loop()

        # if TTS_PROVIDER == "elevenlabs":
        #     import os
        #     voice_id = os.getenv("ELEVENLABS_VOICE_ID", voice)
        #     mp3_bytes = await cls.synthesize_with_elevenlabs(clean, voice_id)
        #     if mp3_bytes:
        #         return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
        #     logger.warning("ElevenLabs failed, falling back to local TTS")
            
        if TTS_PROVIDER == "edge_tts":
            selected_voice = voice
            if voice in ("en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural"):
                selected_voice = "en-IN-PrabhatNeural"
            lower = clean.lower()
            if any("à¤€" <= ch <= "à¥¿" for ch in clean):
                selected_voice = "hi-IN-MadhurNeural"
            elif any("à®€" <= ch <= "à¯¿" for ch in clean):
                selected_voice = "ta-IN-ValluvarNeural"
            else:
                words = set(lower.split())
                hindi_markers = {"namaste", "haan", "bilkul", "aapko", "kaunsa", "bataiye", "karenge", "bhej", "sakein", "theek", "shukriya", "kya", "main"}
                tamil_markers = {"vanakkam", "nandri", "pesurom", "irundhu", "ungalukku", "venuma"}
                if len(words.intersection(hindi_markers)) >= 2:
                    selected_voice = "hi-IN-MadhurNeural"
                elif len(words.intersection(tamil_markers)) >= 1:
                    selected_voice = "ta-IN-ValluvarNeural"

            mp3_bytes = await cls.synthesize_with_edge_tts(clean, selected_voice, speed)
            if mp3_bytes:
                return await loop.run_in_executor(None, _mp3_to_pcm16k, mp3_bytes)
            logger.warning("Edge-TTS failed, falling back to local TTS")

        # Kokoro path (both "kokoro" and "kokoro_clone" providers, plus Edge-TTS fallback)
        voice_to_use = "my_voice" if TTS_PROVIDER == "kokoro_clone" else "hm_omega"
        return await loop.run_in_executor(
            None,
            KokoroTTS.synthesize_to_pcm,
            clean,
            voice_to_use,
            speed,
        )


def _mp3_to_pcm16k(mp3_bytes: bytes) -> bytes:
    """
    Convert MP3 bytes to 16kHz 16-bit mono PCM bytes.

    Uses soundfile + io.BytesIO. Falls back to raw decoding if soundfile
    cannot handle the format (rare for Edge-TTS output).

    Note: soundfile requires libsndfile which supports MP3 only in recent
    versions. If this fails, install pydub + ffmpeg as alternative.
    """
    try:
        buf = io.BytesIO(mp3_bytes)
        samples, sr = sf.read(buf, dtype="float32")
        # Convert stereo to mono if needed
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        # Resample to 16kHz
        samples = _resample(samples, sr, TARGET_SAMPLE_RATE)
        return _float32_to_pcm16(samples)
    except Exception:
        # soundfile can't decode MP3 without libsndfile MP3 support
        # Try pydub as fallback (requires ffmpeg)
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
            seg = seg.set_channels(1).set_frame_rate(TARGET_SAMPLE_RATE).set_sample_width(2)
            return seg.raw_data
        except Exception as e2:
            logger.error("MP3-to-PCM conversion failed: %s", e2)
            return b""


async def tts_worker(
    response_queue: asyncio.Queue,
    audio_queue: asyncio.Queue,
    tenant_id: str,
    lead_id: str,
) -> None:
    """
    Async TTS worker: consumes LLM response text from response_queue,
    synthesizes each sentence independently, and streams PCM audio chunks
    to audio_queue for WebSocket delivery.

    CRITICAL DESIGN: Sentence-level streaming
    ==========================================
    Instead of synthesizing the full response before sending audio, this worker
    splits the response into sentences and synthesizes + enqueues each sentence
    as soon as it's available. This means:
      - First audio chunk reaches the client ~300-500ms after STT completes
      - The user hears the agent speaking while later sentences are still synthesizing
      - This is essential for achieving <1s voice-to-voice latency

    Queue protocol:
      - Input (response_queue): dict with keys:
          "response"   : str  -- full agent response text
          "user_text"  : str  -- what the user said (for logging)
          "tenant_id"  : str
          "lead_id"    : str
      - Output (audio_queue): dict with keys:
          "pcm"        : bytes  -- raw 16kHz 16-bit mono PCM
          "text"       : str    -- sentence text (for transcript display)
          "tenant_id"  : str
          "lead_id"    : str
      - Sentinel: None in response_queue --> puts None in audio_queue --> stops audio sender

    Args:
        response_queue: Async queue receiving LLM responses (from llm_worker).
        audio_queue:    Async queue for synthesized audio chunks (to WebSocket sender).
        tenant_id:      Tenant identifier for logging.
        lead_id:        Lead identifier for logging.
    """
    from backend.voice.text_utils import iter_sentences

    logger.info("TTS worker started [%s/%s] provider=%s", tenant_id, lead_id, TTS_PROVIDER)
    loop = asyncio.get_event_loop()

    try:
        while True:
            item = await response_queue.get()

            # Sentinel check: None means pipeline is shutting down
            if item is None:
                logger.info("TTS worker stopping [%s/%s]", tenant_id, lead_id)
                response_queue.task_done()
                await audio_queue.put(None)  # Propagate sentinel to audio sender
                break

            response_text = item.get("response", "")
            if not response_text.strip():
                response_queue.task_done()
                continue

            logger.info("TTS synthesizing [%s/%s]: '%s'", tenant_id, lead_id, response_text[:80])

            sentence_count = 0

            if TTS_PROVIDER == "chatterbox_clone":
                # â”€â”€ Dual-Track Pipeline: race-to-play + pre-synthesis queue â”€â”€
                from backend.voice.chatterbox_pipeline import create_synthesizer
                synth = create_synthesizer()
                await synth.start()

                # Feed all sentences into synthesizer upfront
                for sentence in iter_sentences(response_text):
                    sentence = sentence.strip()
                    if sentence:
                        await synth.push(sentence)
                await synth.close()  # signals end of input

                # Drain synthesized audio in order
                while True:
                    pcm = await synth.next_audio()
                    if pcm is None:
                        break
                    # Find corresponding sentence for transcript display
                    sentence_count += 1
                    await audio_queue.put({
                        "tenant_id": tenant_id,
                        "lead_id":   lead_id,
                        "pcm":       pcm,
                        "text":      response_text,
                    })
            else:
                # â”€â”€ Standard path: edge_tts / kokoro per sentence â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                for sentence in iter_sentences(response_text):
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    pcm = await KokoroTTS.route_tts(
                        sentence,
                        TTS_VOICE,
                        TTS_SPEED,
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
                "TTS [%s/%s]: %d sentence(s) synthesized from '%s'",
                tenant_id, lead_id, sentence_count, response_text[:60],
            )
            response_queue.task_done()

    except asyncio.CancelledError:
        logger.info("TTS worker cancelled [%s/%s]", tenant_id, lead_id)


_GREETING_CACHE: dict = {}

async def get_cached_greeting_pcm(text: str, voice: str = "en-IN-NeerjaNeural") -> bytes:
    key = (text, voice)
    if key in _GREETING_CACHE:
        return _GREETING_CACHE[key]
    pcm = await KokoroTTS.synthesize_to_pcm_async(text, voice=voice)
    if pcm:
        _GREETING_CACHE[key] = pcm
    return pcm


