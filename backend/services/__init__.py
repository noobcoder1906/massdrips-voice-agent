"""backend/services/__init__.py — Re-export all service functions."""
from backend.services.services import (
    create_tenant, get_tenant, get_all_tenants, update_tenant, get_tenant_persona,
    create_lead, get_lead, get_leads_for_tenant, update_lead_after_call, get_lead_context,
    create_product, get_products_for_tenant, search_products,
    create_call_log, append_transcript, close_call_log,
)
from backend.services.campaign_service import (
    create_campaign, get_campaign, get_campaigns_for_tenant, update_campaign_status,
    add_leads_to_campaign, get_active_campaigns, update_campaign_lead_state
)

__all__ = [
    "create_tenant", "get_tenant", "get_all_tenants", "update_tenant", "get_tenant_persona",
    "create_lead", "get_lead", "get_leads_for_tenant", "update_lead_after_call", "get_lead_context",
    "create_product", "get_products_for_tenant", "search_products",
    "create_call_log", "append_transcript", "close_call_log",
    "create_campaign", "get_campaign", "get_campaigns_for_tenant", "update_campaign_status",
    "add_leads_to_campaign", "get_active_campaigns", "update_campaign_lead_state",
]
