"""
backend/telephony/factory.py

Factory function for instantiating Telephony Providers.
Supported providers: 'mock', 'twilio', 'exotel'.
"""

from typing import Optional, Dict, Any
from backend.telephony.base import TelephonyProvider
from backend.telephony.mock_provider import MockTelephonyProvider
from backend.telephony.twilio_provider import TwilioTelephonyProvider


def get_telephony_provider(
    provider_name: str = "mock",
    config: Optional[Dict[str, Any]] = None
) -> TelephonyProvider:
    """
    Returns an instance of TelephonyProvider based on provider_name.
    """
    provider_key = (provider_name or "mock").lower()
    if provider_key == "twilio":
        return TwilioTelephonyProvider(config or {})
    elif provider_key == "mock":
        return MockTelephonyProvider(config or {})
    else:
        # Default fallback to Mock
        return MockTelephonyProvider(config or {})
