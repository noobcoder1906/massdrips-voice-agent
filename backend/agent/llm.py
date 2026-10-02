"""
backend/agent/llm.py

Async streaming Ollama LLM client for VoxSales.
Zero API cost — runs models fully on-device via Ollama.

Model configured via .env:
  OLLAMA_HOST  = http://localhost:11434
  OLLAMA_MODEL = llama3.2:3b   (fast, fits in 4GB RAM)

Streaming flow:
  transcript string
      │
      ▼
  OllamaLLM.stream_response()
      │  yields text tokens
      ▼
  LLM worker → response_queue
"""

import asyncio
import logging
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


class GroqLLM:
    """Async streaming Groq Cloud LLM client for ultra-low-latency voice responses (<100ms)."""

    def __init__(self):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=GROQ_API_KEY)
        logger.info(f"GroqLLM initialized with model={GROQ_MODEL}")

    async def check_connection(self) -> bool:
        return bool(GROQ_API_KEY)

    async def stream_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        messages = (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [{"role": "user", "content": user_message}]
        )

        logger.info(
            f"Groq LLM request: model={GROQ_MODEL}, "
            f"history_len={len(conversation_history)}, "
            f"user='{user_message[:60]}...'"
        )

        try:
            stream = await self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                stream=True,
                temperature=0.6,
                max_tokens=400,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    yield token
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            yield "Sorry, I'm having trouble connecting. Could you say that again?"


class OllamaLLM:
    """Async wrapper around local Ollama client."""

    def __init__(self):
        import ollama
        self._client = ollama.AsyncClient(host=OLLAMA_HOST)
        logger.info(
            f"OllamaLLM initialized: host={OLLAMA_HOST}, model={OLLAMA_MODEL}"
        )

    async def check_connection(self) -> bool:
        try:
            await self._client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama not reachable at {OLLAMA_HOST}: {e}")
            return False

    async def stream_response(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        messages = (
            [{"role": "system", "content": system_prompt}]
            + conversation_history
            + [{"role": "user", "content": user_message}]
        )

        logger.info(
            f"Ollama LLM request: model={OLLAMA_MODEL}, "
            f"history_len={len(conversation_history)}, "
            f"user='{user_message[:60]}...'"
        )

        try:
            async for chunk in await self._client.chat(
                model=OLLAMA_MODEL,
                messages=messages,
                stream=True,
            ):
                token = chunk["message"]["content"]
                if token:
                    yield token
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield "Sorry, I'm having trouble responding right now. Can you repeat that?"


def get_llm_engine():
    """Factory to get the configured LLM engine."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq" and GROQ_API_KEY:
        return GroqLLM()
    return OllamaLLM()


async def llm_worker(
    transcript_queue: asyncio.Queue,
    response_queue: asyncio.Queue,
    system_prompt: str,
    tenant_id: str,
    lead_id: str,
) -> None:
    """
    Async worker: pulls transcript items from transcript_queue,
    sends them to Ollama streaming LLM, collects the full response,
    and pushes result onto response_queue.

    Maintains per-session conversation history for context memory.

    Args:
        transcript_queue: Source — receives {"transcript": str, ...}
        response_queue:   Sink   — puts {"role": "assistant", "content": str, ...}
        system_prompt:    Built system prompt for this tenant/session.
        tenant_id:        For logging.
        lead_id:          For logging.
    """
    llm = get_llm_engine()
    conversation_history: list[dict] = []

    logger.info(f"LLM worker started [{tenant_id}/{lead_id}]")

    try:
        while True:
            item = await transcript_queue.get()

            if item is None:
                logger.info(f"LLM worker stopping [{tenant_id}/{lead_id}]")
                transcript_queue.task_done()
                await response_queue.put(None)
                break

            user_text = item["transcript"]
            logger.info(f"LLM processing: '{user_text}'")

            # Collect full streaming response
            full_response = ""
            async for token in llm.stream_response(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                user_message=user_text,
            ):
                full_response += token

            full_response = full_response.strip()
            logger.info(f"LLM response: '{full_response[:100]}...'")

            # Update conversation memory
            conversation_history.append(
                {"role": "user", "content": user_text}
            )
            conversation_history.append(
                {"role": "assistant", "content": full_response}
            )

            # Keep history bounded (last 10 turns = 20 messages)
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            # Push to response queue for TTS (Phase 4) / WebSocket relay
            await response_queue.put({
                "tenant_id": tenant_id,
                "lead_id":   lead_id,
                "user_text": user_text,
                "response":  full_response,
            })

            transcript_queue.task_done()

    except asyncio.CancelledError:
        logger.info(f"LLM worker cancelled [{tenant_id}/{lead_id}]")
