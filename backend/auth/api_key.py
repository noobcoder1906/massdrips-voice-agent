"""
backend/auth/api_key.py

API Key authentication & security dependency for public REST API endpoints.
Validates 'x-api-key' header against MongoDB tenant records.
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict, Any
from backend.services import get_all_tenants, get_tenant

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def get_current_tenant_from_key(api_key: Optional[str] = Security(api_key_header)) -> Dict[str, Any]:
    """
    Validates API key header and returns matching tenant document.
    """
    if not api_key:
        # Fallback to default Mass Drips tenant in dev/test mode if header omitted
        tenants = await get_all_tenants()
        if tenants:
            return tenants[0]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'x-api-key' header"
        )

    # Find tenant by API key
    tenants = await get_all_tenants()
    for t in tenants:
        if t.get("api_key") == api_key or t.get("id") == api_key:
            return t

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )
