"""
backend/models.py

MongoDB document schemas using Pydantic v2.
All collections are multi-tenant — every document carries tenant_id.

Collections:
  tenants   — SaaS client config (persona, voice, billing)
  leads     — Individual contacts per tenant
  products  — Product catalog per tenant
  calls     — Call session logs
  campaigns — Bulk outreach campaigns
"""

from datetime import datetime
from typing import Optional, Annotated, Any
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


# ── ObjectId support ───────────────────────────────────────────────────────────
class PyObjectId(str):
    """Pydantic-compatible MongoDB ObjectId field."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, info=None):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)


# ── Tenant (SaaS Client) ───────────────────────────────────────────────────────
class TenantPersona(BaseModel):
    """AI agent persona configuration per tenant."""
    agent_name:    str    = "Aria"
    brand_name:    str    = "VoxSales"
    language:      str    = "english"    # english | hindi | hinglish
    tone:          str    = "friendly"   # friendly | professional | casual
    agent_type:    str    = "sales"      # sales | support | sizing
    max_words:     int    = 60


class TenantCreate(BaseModel):
    name:          str
    email:         str
    phone:         Optional[str] = None
    persona:       TenantPersona = TenantPersona()
    plan:          str = "free"          # free | pro | enterprise
    is_active:     bool = True


class TenantResponse(TenantCreate):
    id:            str
    created_at:    datetime
    updated_at:    datetime


# ── Lead ───────────────────────────────────────────────────────────────────────
class LeadCreate(BaseModel):
    tenant_id:     str
    name:          str
    phone:         str
    email:         Optional[str] = None
    interests:     list[str] = []
    tags:          list[str] = []
    language:      str = "english"
    notes:         Optional[str] = None
    status:        str = "new"           # new | contacted | interested | converted | dnc


class LeadResponse(LeadCreate):
    id:                          str
    lead_score:                  int = 0
    call_count:                  int = 0
    last_call_at:                Optional[datetime] = None
    last_interaction_summary:    Optional[str] = None
    created_at:                  datetime
    updated_at:                  datetime


# ── Product ────────────────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    tenant_id:     str
    name:          str
    price:         float
    currency:      str = "INR"
    description:   str
    category:      Optional[str] = None
    tags:          list[str] = []
    in_stock:      bool = True
    sku:           Optional[str] = None
    size_chart:    Optional[dict] = None   # For sizing agent


class ProductResponse(ProductCreate):
    id:            str
    created_at:    datetime
    updated_at:    datetime


# ── Call Log ───────────────────────────────────────────────────────────────────
class CallLogCreate(BaseModel):
    tenant_id:     str
    lead_id:       str
    campaign_id:   Optional[str] = None
    status:        str = "initiated"     # initiated | active | completed | failed
    direction:     str = "outbound"      # outbound | inbound


class CallLogResponse(CallLogCreate):
    id:            str
    started_at:    datetime
    ended_at:      Optional[datetime] = None
    duration_sec:  int = 0
    transcript:    list[dict] = []       # [{"role":"user"|"agent","text":"...","ts":...}]
    outcome:       Optional[str] = None  # interested | not_interested | callback | converted
    sentiment:     Optional[str] = None  # positive | neutral | negative
    recording_url: Optional[str] = None
    lead_score_delta: int = 0


# ── Campaign ───────────────────────────────────────────────────────────────────
class CampaignCreate(BaseModel):
    tenant_id:     str
    name:          str
    description:   Optional[str] = None
    lead_ids:      list[str] = []
    script_prompt: Optional[str] = None
    status:        str = "draft"         # draft | running | paused | completed
    max_concurrent_calls: int = 5
    retry_count:   int = 2


class CampaignResponse(CampaignCreate):
    id:            str
    total_leads:   int = 0
    calls_made:    int = 0
    calls_answered:int = 0
    conversions:   int = 0
    created_at:    datetime
    updated_at:    datetime


# ── Generic API response ───────────────────────────────────────────────────────
class APIResponse(BaseModel):
    success:   bool
    message:   str
    data:      Optional[Any] = None
