"""
backend/agent/lead_scorer.py

AI Lead Scoring Engine.
Evaluates call transcripts post-session to calculate:
  1. Lead Score (0-100) based on interest, sizing inquiries, budget match, and buy intent
  2. Call Sentiment ('positive', 'neutral', 'negative')
  3. Call Outcome ('converted', 'interested', 'callback', 'not_interested', 'dnc')
  4. Executive 1-sentence AI Summary
"""

import re
from typing import List, Dict, Any


def evaluate_call_transcript(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes conversation transcript and returns score, sentiment, outcome, and summary.
    """
    if not transcript:
        return {
            "score": 0,
            "sentiment": "neutral",
            "outcome": "no_answer",
            "summary": "Call ended before dialogue took place.",
            "buying_signals": [],
            "objections": []
        }

    full_text = " ".join([item.get("text", "") for item in transcript]).lower()
    user_turns = [item.get("text", "") for item in transcript if item.get("role") == "user"]
    user_text = " ".join(user_turns).lower()

    # Buying signals keywords
    buying_keywords = [
        "price", "cost", "kitne ka hai", "rupees", "inr", "discount", "offer", "code",
        "buy", "order", "kharidna", "size", "xl", "l", "m", "s", "medium", "large",
        "stock", "available", "color", "black", "delivery", "kab aayega", "cod", "cash on delivery"
    ]

    # Objection keywords
    objection_keywords = [
        "mehanga", "expensive", "too high", "not interested", "zaroorat nahi",
        "don't call", "stop calling", "remove my number", "wrong number"
    ]

    buying_count = sum(1 for kw in buying_keywords if re.search(r'\b' + re.escape(kw) + r'\b', user_text))
    objection_count = sum(1 for kw in objection_keywords if re.search(r'\b' + re.escape(kw) + r'\b', user_text))

    # Base score computation
    score = 30  # Base score for answering call
    score += min(buying_count * 15, 55)

    if len(user_turns) >= 3:
        score += 15

    # Sentiment analysis
    if buying_count >= 2 and objection_count == 0:
        sentiment = "positive"
        score += 10
    elif objection_count >= 2:
        sentiment = "negative"
        score = max(5, score - 30)
    else:
        sentiment = "neutral"

    # Outcome determination
    if any(kw in user_text for kw in ["order kar do", "book kar do", "kharidunga", "send link", "buy now"]):
        outcome = "converted"
        score = max(score, 90)
    elif any(kw in user_text for kw in ["baad me call", "call back", "kal bataunga", "think about it"]):
        outcome = "callback"
        score = max(score, 60)
    elif any(kw in user_text for kw in ["don't call", "remove my number", "not interested"]):
        outcome = "dnc" if "remove" in user_text or "stop" in user_text else "not_interested"
        score = 10
    elif buying_count > 0:
        outcome = "interested"
    else:
        outcome = "not_interested"

    score = max(0, min(100, score))

    summary = f"Customer expressed {sentiment} sentiment with {buying_count} buying signals. Outcome: {outcome}."

    return {
        "score": score,
        "sentiment": sentiment,
        "outcome": outcome,
        "summary": summary,
        "buying_signals_count": buying_count,
        "objections_count": objection_count
    }
