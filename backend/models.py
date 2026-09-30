from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

# Helper for MongoDB ObjectId string representation
def generate_uuid() -> str:
    return str(uuid4())

class Tenant(BaseModel):
    """A client business using VoxSales."""
    id: str = Field(default_factory=generate_uuid, alias="_id")
    name: str
    slug: str
    industry: Optional[str] = None
    plan: str = "starter"
    telephony_provider: str = "twilio"
    telephony_config: Dict[str, Any] = {}
    monthly_call_limit: int = 500
    calls_used_this_month: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    """A dashboard user within a tenant."""
    id: str = Field(default_factory=generate_uuid, alias="_id")
    tenant_id: str
    email: EmailStr
    password_hash: str
    role: str = "member"
    is_active: bool = True

class Lead(BaseModel):
    """A lead/contact that the agent will call."""
    id: str = Field(default_factory=generate_uuid, alias="_id")
    tenant_id: str
    name: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None
    city: Optional[str] = None
    interests: List[str] = []
    custom_data: Dict[str, Any] = {}
    lead_score: int = 0
    status: str = "new"  # new, contacted, interested, converted, declined
    dnd_status: bool = False
    conversation_history: List[Dict[str, Any]] = [] # Storing call summaries directly here
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Campaign(BaseModel):
    """An outbound calling campaign targeting multiple leads."""
    id: str = Field(default_factory=generate_uuid, alias="_id")
    tenant_id: str
    persona_id: str
    name: str
    status: str = "draft"
    target_products: List[str] = []
    discount_code: Optional[str] = None
    max_concurrent_calls: int = 3
    retry_attempts: int = 3
    total_leads: int = 0
    leads_called: int = 0
    leads_converted: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentPersona(BaseModel):
    """Per-tenant AI agent configuration."""
    id: str = Field(default_factory=generate_uuid, alias="_id")
    tenant_id: str
    name: str = "SalesBot"
    voice_id: str = "af_heart"
    language: str = "en"
    system_prompt: str
    greeting_script: str
    objection_responses: Dict[str, List[str]] = {}
    max_call_duration_sec: int = 300
    personality_traits: List[str] = []
