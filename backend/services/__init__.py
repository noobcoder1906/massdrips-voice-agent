"""backend/services/__init__.py — Re-export all service functions."""
from backend.services.services import (
    create_tenant, get_tenant, get_all_tenants, update_tenant, get_tenant_persona,
    create_lead, get_lead, get_leads_for_tenant, update_lead_after_call, get_lead_context,
    create_product, get_products_for_tenant, search_products,
    create_call_log, append_transcript, close_call_log,
)

__all__ = [
    "create_tenant", "get_tenant", "get_all_tenants", "update_tenant", "get_tenant_persona",
    "create_lead", "get_lead", "get_leads_for_tenant", "update_lead_after_call", "get_lead_context",
    "create_product", "get_products_for_tenant", "search_products",
    "create_call_log", "append_transcript", "close_call_log",
]
