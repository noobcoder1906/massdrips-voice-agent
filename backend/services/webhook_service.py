"""
backend/services/webhook_service.py

CRM Webhook Dispatch Engine.
Sends real-time HTTP POST JSON payloads to tenant webhook URLs upon call completion.
"""

import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("webhook_service")


async def dispatch_call_webhook(webhook_url: str, payload: Dict[str, Any]) -> bool:
    """
    Sends async HTTP POST request to client's webhook endpoint.
    """
    if not webhook_url:
        return False

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "VoxSales-Webhook/2.0"},
                timeout=5.0
            )
            logger.info(f"Webhook dispatched to {webhook_url} -> Status {res.status_code}")
            return res.status_code in (200, 201, 202, 204)
        except Exception as e:
            logger.error(f"Webhook dispatch error for {webhook_url}: {e}")
            return False
