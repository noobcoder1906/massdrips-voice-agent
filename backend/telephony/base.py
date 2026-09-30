"""
backend/telephony/base.py

Abstract base class for Telephony Providers (Twilio, Exotel, Mock).
Enables swappable phone call backends with zero code changes to the campaign engine.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class CallResult(BaseModel):
    call_sid: str
    status: str              # queued | initiated | ringing | in-progress | completed | failed | busy | no-answer
    provider: str            # mock | twilio | exotel
    to_phone: str
    from_phone: str
    cost: float = 0.0
    error_message: Optional[str] = None


class TelephonyProvider(ABC):
    """Abstract Telephony Provider Interface."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def make_outbound_call(
        self,
        to_phone: str,
        from_phone: str,
        websocket_url: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        """
        Trigger an outbound call and connect it to our WebSocket audio stream.
        """
        pass

    @abstractmethod
    async def end_call(self, call_sid: str) -> bool:
        """Terminate an active call by call_sid."""
        pass

    @abstractmethod
    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        """Fetch current status and metrics for a call."""
        pass

    @abstractmethod
    def get_cost_per_minute(self) -> float:
        """Return provider cost per minute (in USD or INR)."""
        pass
