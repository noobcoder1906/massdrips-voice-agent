"""
backend/voice/text_utils.py

Text preprocessing utilities for TTS.
Cleans LLM output to make it voice-friendly before synthesis.

Key operations:
  1. Strip markdown formatting (asterisks, bullets, headers)
  2. Expand common abbreviations (₹ → rupees, etc.)
  3. Split text into sentence chunks for streaming synthesis
"""

import re
from typing import Generator


# ── Abbreviation/Symbol expansion ─────────────────────────────────────────────
SYMBOL_MAP = {
    "₹":   "rupees",
    "$":   "dollars",
    "%":   "percent",
    "&":   "and",
    "@":   "at",
    "w/":  "with",
    "w/o": "without",
    "vs.": "versus",
    "vs":  "versus",
    "etc.":"etcetera",
    "approx.": "approximately",
}

# Sentence boundary regex — splits on . ! ? followed by space or end
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def clean_for_tts(text: str) -> str:
    """
    Clean LLM output text for TTS synthesis.

    Removes markdown, normalizes symbols, collapses whitespace.

    Args:
        text: Raw LLM response string.

    Returns:
        Clean, speakable plain text string.
    """
    if not text:
        return ""

    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bold/italic markers (**text**, *text*, __text__, _text_)
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)

    # Remove bullet points and numbered lists
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove inline code and code blocks
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # Remove markdown links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Expand symbols
    for symbol, replacement in SYMBOL_MAP.items():
        text = text.replace(symbol, f" {replacement} ")

    # Normalize rupee amounts: "1,299" → "1299" for natural speech
    text = re.sub(r'(\d),(\d{3})', r'\1\2', text)

    # Collapse multiple spaces/newlines into single space
    text = re.sub(r'[\n\r]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)

    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    """
    Split cleaned text into sentence-level chunks for streaming TTS.

    Returns chunks of 1-2 sentences for low-latency audio delivery.
    Empty or very short chunks are filtered out.

    Args:
        text: Pre-cleaned text (run through clean_for_tts first).

    Returns:
        List of sentence strings.
    """
    if not text:
        return []

    # Primary split on sentence boundaries
    raw_sentences = SENTENCE_SPLIT_RE.split(text)

    sentences = []
    buffer = ""

    for sent in raw_sentences:
        sent = sent.strip()
        if not sent:
            continue

        # Pair very short sentences together for natural cadence
        if len(buffer) + len(sent) < 80:
            buffer = (buffer + " " + sent).strip() if buffer else sent
        else:
            if buffer:
                sentences.append(buffer)
            buffer = sent

    if buffer:
        sentences.append(buffer)

    # Filter out anything too short to synthesize meaningfully
    return [s for s in sentences if len(s) > 2]


def iter_sentences(text: str) -> Generator[str, None, None]:
    """Generator version of split_into_sentences for streaming use."""
    for sentence in split_into_sentences(clean_for_tts(text)):
        yield sentence
