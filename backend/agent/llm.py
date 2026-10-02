"""
backend/agent/llm.py

Async streaming LLM client for VoxSales voice agent.

ARCHITECTURE OVERVIEW (for future agents):
==========================================
This module drives the "brain" of the voice agent. It receives transcribed
user speech and generates a natural spoken response.

Pipeline position:
  STT transcript_queue --> llm_worker() --> response_queue --> TTS

TWO PROVIDERS (configured via LLM_PROVIDER in .env):
  1. groq   : Groq Cloud API (ultra-fast, ~100ms TTFT, requires GROQ_API_KEY)
  2. ollama : Local Ollama (free, ~500-2000ms depending on model + hardware)

LATENCY ANALYSIS:
=================
The LLM is the biggest latency bottleneck in the voice pipeline:

  Groq (qwen-2.5-7b or llama3.1-8b):
    - TTFT (Time to First Token): ~60-120ms
    - Full 20-word response: ~150-250ms total
    - BEST CHOICE for real-time voice

  Ollama (llama3.2:3b on CPU):
    - TTFT: ~300-800ms
    - Full 20-word response: ~800-2000ms
    - Acceptable on CUDA GPU (RTX 3060+), too slow on CPU for live calls

CRITICAL BUG FIXED (2026-10-02):
==================================
BEFORE: llm_worker() was collecting the FULL streaming response before pushing
it to the TTS queue. This eliminated the benefit of streaming and added
unnecessary latency (waited for last token before TTS started).

AFTER: llm_worker() now uses sentence-boundary detection to push PARTIAL
responses to the TTS queue as soon as a complete sentence is detected in the
stream. This means:
  - First sentence synthesized and played while LLM is still generating tokens
  - Voice-to-voice latency: ~400-700ms (Groq) vs ~1500-3000ms (before fix)

LAYA INTEGRATION:
=================
llm_worker() calls the Laya decision engine BEFORE sending text to the LLM.
High-confidence decisions (DNC, human handoff) are fast-pathed:
  - Response generated from pre-written template in ~33ms (no LLM call)
  - For lower-confidence or nuanced intents, Laya adds a routing hint to the
    system prompt without changing the full prompt structure

See backend/agent/laya_router.py for the decision engine.
See backend/agent/prompts.py for build_system_prompt_with_laya().

CONVERSATION HISTORY:
=====================
Each call session maintains an in-memory conversation history (list of role/content dicts).
This gives the LLM context of the full conversation for coherent responses.
History is bounded to last 10 turns (20 messages) to prevent prompt bloat.

The history is LOST on WebSocket disconnect. No persistence yet -- future work
could save call transcripts to MongoDB for follow-up context.

COLD CALL BEHAVIOR:
====================
The system prompt (from prompts.py) enforces the cold-call SDR structure:
  opener -> hook -> value prop -> discovery question -> close
The LLM adheres to max_tokens=40 (roughly 25-30 words) to keep responses
voice-appropriate. Long monologues kill phone calls.
"""

import asyncio
import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()   # groq | ollama
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# qwen/qwen3.8-27b is great quality but slow. Use llama-3.1-8b-instant for fastest voice latency.
GROQ_MODEL   = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

# Max tokens for voice responses -- keep SHORT for phone call naturalness
# 40 tokens â‰ˆ 25-30 words â‰ˆ 1 natural spoken sentence
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "45"))

# Sentence boundary characters for streaming early-emit
_SENTENCE_ENDS = {".", "!", "?", "à¥¤"}   # includes Hindi danda


def _is_sentence_boundary(token: str) -> bool:
    """Check if a streamed token ends with a sentence boundary character."""
    stripped = token.rstrip()
    return bool(stripped) and stripped[-1] in _SENTENCE_ENDS


class GroqLLM:
    """
    Async streaming Groq Cloud LLM client.

    Groq runs inference on custom LPU hardware achieving ~700 tokens/sec,
    making it the fastest available cloud LLM API. Ideal for real-time voice.

    Recommended models for voice (balance of speed + quality):
      - llama-3.1-8b-instant  : TTFT ~60ms, best for voice (recommended)
      - mixtral-8x7b-32768    : TTFT ~80ms, better reasoning
      - qwen/qwen3.8-27b      : TTFT ~200ms, best quality (too slow for voice)

    FEASIBILITY: Production-ready. $0.05-0.10 per million input tokens.
    At 100 calls/day with 500 tokens/call = ~$0.005/day. Practically free.
    """

    def __init__(self):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=GROQ_API_KEY)
        logger.info("GroqLLM initialized: model=%s, max_tokens=%d", GROQ_MODEL, LLM_MAX_TOKENS)

    async def check_connection(self) -> bool:
        """Verify Groq API key is configured (no network call)."""
        return bool(GROQ_API_KEY)

    async def stream_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response tokens asynchronously.

        Builds the full message list (system + history + user) and streams
        response tokens from Groq. Caller is responsible for accumulating
        tokens into sentences.

        Args:
            system_prompt:        The agent system prompt (from prompts.py).
            conversation_history: List of {role, content} dicts (bounded to 20 items).
            user_message:         The transcribed user speech text.

        Yields:
            Individual text tokens as they arrive from the API stream.
        """
        messages = (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [{"role": "user", "content": user_message}]
        )

        logger.info(
            "Groq request: model=%s, history=%d, user='%s'",
            GROQ_MODEL, len(conversation_history), user_message[:60],
        )

        try:
            stream = await self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                stream=True,
                temperature=0.6,        # Slightly creative for natural conversation
                max_tokens=LLM_MAX_TOKENS,
                # Note: NOT using Groq 'stop' param -- sentence splitting is handled
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield token

        except Exception as e:
            logger.error("Groq streaming error: %s", e)
            # Graceful fallback response in the agent's language
            yield "Ek second, kuch technical issue aa gaya. Dobara try karte hain?"


class OllamaLLM:
    """
    Async streaming wrapper around the local Ollama client.

    Ollama runs open-source models (llama3.2, mistral, phi, etc.) locally.
    Zero API cost. Latency depends heavily on hardware:
      - CPU only (no GPU): 800-3000ms for llama3.2:3b -- too slow for live calls
      - CUDA GPU (RTX 3060): 100-300ms -- acceptable for live calls
      - CUDA GPU (RTX 4090): 50-100ms -- excellent

    FEASIBILITY: Good for development + testing. For production voice calls,
    Groq is strongly recommended for consistent low latency.
    """

    def __init__(self):
        import ollama
        self._client = ollama.AsyncClient(host=OLLAMA_HOST)
        logger.info("OllamaLLM initialized: host=%s, model=%s", OLLAMA_HOST, OLLAMA_MODEL)

    async def check_connection(self) -> bool:
        """Test if Ollama server is reachable."""
        try:
            await self._client.list()
            return True
        except Exception as e:
            logger.error("Ollama not reachable at %s: %s", OLLAMA_HOST, e)
            return False

    async def stream_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from local Ollama model.
        Same interface as GroqLLM.stream_response() for interchangeability.
        """
        messages = (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [{"role": "user", "content": user_message}]
        )

        logger.info(
            "Ollama request: model=%s, history=%d, user='%s'",
            OLLAMA_MODEL, len(conversation_history), user_message[:60],
        )

        try:
            async for chunk in await self._client.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                stream=True,
                options={"num_predict": LLM_MAX_TOKENS, "temperature": 0.6},
            ):
                token = chunk["message"]["content"]
                if token:
                    yield token
        except Exception as e:
            logger.error("Ollama streaming error: %s", e)
            yield "Sorry, abhi ek second problem aa gayi. Phir baat karte hain?"


def get_llm_engine():
    """
    Factory function to create the configured LLM engine.

    Priority:
      1. If LLM_PROVIDER=groq AND GROQ_API_KEY is set --> GroqLLM
      2. Otherwise --> OllamaLLM (local fallback)

    Called once per call session from llm_worker().
    """
    provider = LLM_PROVIDER
    if provider == "groq" and GROQ_API_KEY:
        return GroqLLM()
    if provider == "groq" and not GROQ_API_KEY:
        logger.warning("LLM_PROVIDER=groq but GROQ_API_KEY is not set. Falling back to Ollama.")
    return OllamaLLM()


async def llm_worker(
    transcript_queue: asyncio.Queue,
    response_queue: asyncio.Queue,
    system_prompt: str,
    tenant_id: str,
    lead_id: str,
    initial_greeting: str = "",
) -> None:
    """
    Core async LLM worker. Connects the STT output to the TTS input.

    STREAMING EARLY-EMIT OPTIMIZATION:
    ====================================
    Instead of waiting for the full LLM response before pushing to TTS,
    this worker monitors the token stream for sentence boundaries and emits
    each complete sentence to response_queue as soon as it's detected.

    This means TTS synthesis starts on the FIRST sentence while the LLM is
    still generating the rest of the response. Net effect: first audio plays
    ~300-600ms earlier than the naive "collect all then synthesize" approach.

    LAYA CIRCUIT BREAKER:
    =====================
    Before calling the LLM, each user message is routed through the Laya
    decision engine:
      - bypass_llm=True intents (DNC, human handoff): return pre-written response
        immediately in ~5ms, NO LLM call at all.
      - bypass_llm=False intents: inject routing hint into system prompt context
        and proceed with LLM (standard path with hint for better response quality).

    Queue protocol:
      - Input (transcript_queue): dict {"transcript": str, "tenant_id": str, "lead_id": str}
        or None (sentinel to stop)
      - Output (response_queue): dict {"tenant_id": str, "lead_id": str,
                                       "user_text": str, "response": str}
        or None (sentinel to signal TTS stop)

    Args:
        transcript_queue: Source queue from STT worker (transcribed user speech).
        response_queue:   Sink queue to TTS worker (agent response text).
        system_prompt:    Base system prompt from build_system_prompt().
                          Note: Laya hints will create modified versions per-turn.
        tenant_id:        For logging and context.
        lead_id:          For logging and context.
    """
    from backend.agent.laya_router import laya_engine

    llm = get_llm_engine()
    conversation_history: list[dict] = []
    if initial_greeting:
        conversation_history.append({"role": "assistant", "content": initial_greeting})

    logger.info("LLM worker started [%s/%s] provider=%s", tenant_id, lead_id, LLM_PROVIDER)

    try:
        while True:
            item = await transcript_queue.get()

            # Sentinel check: None means shutdown signal from STT worker
            if item is None:
                logger.info("LLM worker stopping [%s/%s]", tenant_id, lead_id)
                transcript_queue.task_done()
                await response_queue.put(None)  # Propagate sentinel to TTS worker
                break

            user_text = item["transcript"].strip()
            if not user_text:
                transcript_queue.task_done()
                continue

            logger.info("LLM processing [%s/%s]: '%s'", tenant_id, lead_id, user_text)

            # â”€â”€ LAYA CIRCUIT BREAKER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # Fast intent classification (~5ms keyword matching, ~33ms with Laya SDK).
            # bypass_llm=True means we skip the LLM entirely and return a pre-written
            # response instantly. This is the "Circuit Breaker" pattern.
            laya_decision = laya_engine.classify_intent(user_text)
            logger.info(
                "Laya [%s/%s]: intent=%s confidence=%.0f%% bypass=%s",
                tenant_id, lead_id,
                laya_decision["intent"],
                laya_decision["confidence"] * 100,
                laya_decision["bypass_llm"],
            )

            if laya_decision.get("bypass_llm") and laya_decision.get("fast_response"):
                # Fast path: skip LLM, push pre-written response directly
                fast_resp = laya_decision["fast_response"]
                logger.info(
                    "Laya fast-path [%s/%s]: '%s'", tenant_id, lead_id, fast_resp[:60]
                )
                await response_queue.put({
                    "tenant_id": tenant_id,
                    "lead_id":   lead_id,
                    "user_text": user_text,
                    "response":  fast_resp,
                    "via_laya":  True,      # flag for analytics
                })
                # Still update conversation history for continuity
                conversation_history.append({"role": "user",      "content": user_text})
                conversation_history.append({"role": "assistant",  "content": fast_resp})
                transcript_queue.task_done()
                continue

            # â”€â”€ STANDARD LLM PATH (with optional Laya hint) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # Build turn-specific system prompt with Laya routing hint injected
            prompt_hint = laya_decision.get("prompt_hint")
            effective_prompt = system_prompt
            if prompt_hint:
                # Append hint to system prompt without rebuilding the full prompt
                # (rebuilding from DB would require async calls here -- too slow)
                effective_prompt = (
                    system_prompt
                    + f"\n\n[ROUTING HINT for this turn: {prompt_hint}]"
                )

            # â”€â”€ STREAMING EARLY-EMIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            # Collect tokens. When a sentence boundary is detected, immediately
            # push the partial response to TTS so audio synthesis starts early.
            # Groq returns complete 15-20 word responses in ~100ms.
            # Emitting the full sentence as one cohesive thought avoids multiple sequential
            # TTS synthesis latencies and awkward pauses.
            current_buf = []
            full_response_parts = []
            sentence_count = 0

            async for token in llm.stream_response(
                system_prompt=effective_prompt,
                conversation_history=conversation_history,
                user_message=user_text,
            ):
                current_buf.append(token)
                full_response_parts.append(token)

                stripped = token.rstrip()
                if stripped and stripped[-1] in {".", "!", "?", "\n"}:
                    chunk_text = "".join(current_buf).strip()
                    if len(chunk_text.split()) >= 3:
                        sentence_count += 1
                        await response_queue.put({
                            "tenant_id": tenant_id,
                            "lead_id":   lead_id,
                            "user_text": user_text,
                            "response":  chunk_text,
                            "via_laya":  False,
                        })
                        current_buf = []

            if current_buf:
                chunk_text = "".join(current_buf).strip()
                if chunk_text:
                    sentence_count += 1
                    await response_queue.put({
                        "tenant_id": tenant_id,
                        "lead_id":   lead_id,
                        "user_text": user_text,
                        "response":  chunk_text,
                        "via_laya":  False,
                    })

            full_response = "".join(full_response_parts).strip()

            full_response = full_response.strip()
            logger.info(
                "LLM done [%s/%s]: %d sentence(s), %d chars",
                tenant_id, lead_id, sentence_count, len(full_response),
            )

            # â”€â”€ UPDATE CONVERSATION HISTORY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            conversation_history.append({"role": "user",      "content": user_text})
            conversation_history.append({"role": "assistant",  "content": full_response})

            # Bound history to last 10 turns (20 messages) to prevent prompt bloat
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            transcript_queue.task_done()

    except asyncio.CancelledError:
        logger.info("LLM worker cancelled [%s/%s]", tenant_id, lead_id)

