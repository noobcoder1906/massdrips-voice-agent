"""
backend/telephony/mock_provider.py

Mock Telephony Provider for local testing, CI/CD, and simulated outbound voice calls.
Generates simulated call SIDs and tracks call states without calling real numbers.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any
from backend.telephony.base import TelephonyProvider, CallResult


class MockTelephonyProvider(TelephonyProvider):
    """Simulated telephony provider for offline dev and testing."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.active_calls: Dict[str, Dict[str, Any]] = {}

    async def make_outbound_call(
        self,
        to_phone: str,
        from_phone: str,
        websocket_url: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        call_sid = f"MCK_{uuid.uuid4().hex[:12]}"
        call_info = {
            "call_sid": call_sid,
            "status": "initiated",
            "to_phone": to_phone,
            "from_phone": from_phone,
            "websocket_url": websocket_url,
            "custom_data": custom_data or {},
        }
        self.active_calls[call_sid] = call_info

        # Simulate brief network delay
        await asyncio.sleep(0.05)
        call_info["status"] = "in-progress"

        return CallResult(
            call_sid=call_sid,
            status="initiated",
            provider="mock",
            to_phone=to_phone,
            from_phone=from_phone,
            cost=0.0
        )

    async def end_call(self, call_sid: str) -> bool:
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["status"] = "completed"
            return True
        return False

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        return self.active_calls.get(call_sid, {"call_sid": call_sid, "status": "unknown"})

    def get_cost_per_minute(self) -> float:
        return 0.0
