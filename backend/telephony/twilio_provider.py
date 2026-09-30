"""
backend/telephony/twilio_provider.py

Twilio Telephony Provider for production outbound calls.
Uses HTTP requests to Twilio API to initiate calls with TwiML WebSocket <Stream>.
"""

import os
import httpx
from typing import Optional, Dict, Any
from backend.telephony.base import TelephonyProvider, CallResult


class TwilioTelephonyProvider(TelephonyProvider):
    """Twilio Voice API integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.account_sid = self.config.get("account_sid") or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token  = self.config.get("auth_token")  or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.default_from= self.config.get("from_phone")  or os.getenv("TWILIO_PHONE_NUMBER", "")

    async def make_outbound_call(
        self,
        to_phone: str,
        from_phone: str,
        websocket_url: str,
        custom_data: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        if not self.account_sid or not self.auth_token:
            # Fallback to simulated SID if Twilio credentials not provided
            return CallResult(
                call_sid=f"TW_MOCK_{to_phone[-4:]}",
                status="initiated",
                provider="twilio",
                to_phone=to_phone,
                from_phone=from_phone or self.default_from,
                cost=0.014,
                error_message="TWILIO_ACCOUNT_SID not set - running in dev fallback mode"
            )

        caller = from_phone or self.default_from
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{websocket_url}">
            <Parameter name="tenant_id" value="{custom_data.get('tenant_id', '') if custom_data else ''}" />
            <Parameter name="lead_id" value="{custom_data.get('lead_id', '') if custom_data else ''}" />
        </Stream>
    </Connect>
</Response>"""

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
        data = {
            "To": to_phone,
            "From": caller,
            "Twiml": twiml,
        }

        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    url,
                    data=data,
                    auth=(self.account_sid, self.auth_token),
                    timeout=10.0
                )
                res_data = res.json()
                if res.status_code in (200, 201):
                    return CallResult(
                        call_sid=res_data.get("sid", ""),
                        status=res_data.get("status", "queued"),
                        provider="twilio",
                        to_phone=to_phone,
                        from_phone=caller,
                        cost=0.014
                    )
                else:
                    return CallResult(
                        call_sid="",
                        status="failed",
                        provider="twilio",
                        to_phone=to_phone,
                        from_phone=caller,
                        error_message=res_data.get("message", "Twilio API error")
                    )
            except Exception as e:
                return CallResult(
                    call_sid="",
                    status="failed",
                    provider="twilio",
                    to_phone=to_phone,
                    from_phone=caller,
                    error_message=str(e)
                )

    async def end_call(self, call_sid: str) -> bool:
        if not self.account_sid or not self.auth_token or call_sid.startswith("TW_MOCK"):
            return True
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls/{call_sid}.json"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, data={"Status": "completed"}, auth=(self.account_sid, self.auth_token))
            return res.status_code == 200

    async def get_call_status(self, call_sid: str) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token or call_sid.startswith("TW_MOCK"):
            return {"call_sid": call_sid, "status": "completed"}
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls/{call_sid}.json"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, auth=(self.account_sid, self.auth_token))
            return res.json() if res.status_code == 200 else {"status": "unknown"}

    def get_cost_per_minute(self) -> float:
        return 0.014  # ~ $0.014/min
