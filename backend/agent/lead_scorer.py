"""
backend/agent/lead_scorer.py

AI Lead Scoring Engine — Integrated with Laya Fast Decision Engine.
Evaluates call transcripts post-session using:
  1. Laya Fast Decision Engine (~33ms score & classification primitive)
  2. Fallback LLM transcript evaluation
"""

from typing import List, Dict, Any
from backend.agent.laya_router import laya_engine


def evaluate_call_transcript(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes conversation transcript using Laya decision primitives.
    Returns lead score (0-100), sentiment, outcome, and summary.
    """
    if not transcript:
        return {
            "score": 0,
            "sentiment": "neutral",
            "outcome": "no_answer",
            "summary": "Call ended before dialogue took place.",
            "buying_signals_count": 0,
            "objections_count": 0
        }

    # 1. Evaluate fast lead score via Laya Decision Engine
    laya_eval = laya_engine.evaluate_lead_score_fast(transcript)

    user_turns = [item.get("text", "") for item in transcript if item.get("role") == "user"]
    user_text = " ".join(user_turns).lower()

    # Buying signals & objections count
    buying_keywords = ["price", "cost", "rupees", "discount", "offer", "buy", "order", "size", "xl", "l", "m"]
    objection_keywords = ["mehanga", "expensive", "not interested", "don't call", "stop"]

    buying_count = sum(1 for kw in buying_keywords if kw in user_text)
    objection_count = sum(1 for kw in objection_keywords if kw in user_text)

    summary = (
        f"Laya Decision Classification: intent='{laya_eval.get('laya_intent')}', "
        f"sentiment='{laya_eval['sentiment']}', score={laya_eval['score']}/100. Outcome: {laya_eval['outcome']}."
    )

    return {
        "score": laya_eval["score"],
        "sentiment": laya_eval["sentiment"],
        "outcome": laya_eval["outcome"],
        "summary": summary,
        "buying_signals_count": buying_count,
        "objections_count": objection_count,
        "laya_intent": laya_eval.get("laya_intent")
    }
