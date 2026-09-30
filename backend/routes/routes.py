"""
backend/routes/tenants.py  — Tenant CRUD
backend/routes/leads.py    — Lead CRUD
backend/routes/products.py — Product CRUD

Combined into one file for Phase 5, split into separate files at Phase 9.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models import (
    TenantCreate, LeadCreate, ProductCreate, APIResponse
)
from backend.services import (
    create_tenant, get_tenant, get_all_tenants, update_tenant,
    create_lead, get_lead, get_leads_for_tenant, update_lead_after_call,
    create_product, get_products_for_tenant, search_products,
)

# ── Routers ────────────────────────────────────────────────────────────────────
tenant_router  = APIRouter(prefix="/api/v1/tenants",  tags=["Tenants"])
lead_router    = APIRouter(prefix="/api/v1/leads",    tags=["Leads"])
product_router = APIRouter(prefix="/api/v1/products", tags=["Products"])


# ══════════════════════════════════════════════════════════════════════════════
# TENANT ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@tenant_router.post("/", response_model=APIResponse, status_code=201)
async def api_create_tenant(body: TenantCreate):
    """Create a new SaaS tenant (client onboarding)."""
    data = body.model_dump()
    result = await create_tenant(data)
    return APIResponse(success=True, message="Tenant created", data=result)


@tenant_router.get("/", response_model=APIResponse)
async def api_list_tenants():
    """List all tenants."""
    tenants = await get_all_tenants()
    return APIResponse(success=True, message=f"{len(tenants)} tenants", data=tenants)


@tenant_router.get("/{tenant_id}", response_model=APIResponse)
async def api_get_tenant(tenant_id: str):
    """Get a single tenant by ID."""
    tenant = await get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return APIResponse(success=True, message="OK", data=tenant)


@tenant_router.patch("/{tenant_id}", response_model=APIResponse)
async def api_update_tenant(tenant_id: str, body: dict):
    """Partial update of tenant config (persona, plan, etc.)."""
    result = await update_tenant(tenant_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return APIResponse(success=True, message="Tenant updated", data=result)


# ══════════════════════════════════════════════════════════════════════════════
# LEAD ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@lead_router.post("/", response_model=APIResponse, status_code=201)
async def api_create_lead(body: LeadCreate):
    """Create a new lead for a tenant."""
    data = body.model_dump()
    result = await create_lead(data)
    return APIResponse(success=True, message="Lead created", data=result)


@lead_router.get("/", response_model=APIResponse)
async def api_list_leads(
    tenant_id: str = Query(..., description="Filter by tenant ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """List leads for a tenant."""
    leads = await get_leads_for_tenant(tenant_id, limit=limit)
    return APIResponse(success=True, message=f"{len(leads)} leads", data=leads)


@lead_router.get("/{lead_id}", response_model=APIResponse)
async def api_get_lead(lead_id: str, tenant_id: Optional[str] = Query(None)):
    """Get a single lead by ID."""
    lead = await get_lead(lead_id, tenant_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return APIResponse(success=True, message="OK", data=lead)


@lead_router.patch("/{lead_id}/call-outcome", response_model=APIResponse)
async def api_update_lead_outcome(
    lead_id: str,
    summary: str = Query(...),
    outcome: Optional[str] = Query(None),
    score_delta: int = Query(0),
):
    """Update a lead's status after a call."""
    await update_lead_after_call(lead_id, summary, outcome, score_delta)
    return APIResponse(success=True, message="Lead updated", data=None)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@product_router.post("/", response_model=APIResponse, status_code=201)
async def api_create_product(body: ProductCreate):
    """Add a product to a tenant's catalog."""
    data = body.model_dump()
    result = await create_product(data)
    return APIResponse(success=True, message="Product created", data=result)


@product_router.get("/", response_model=APIResponse)
async def api_list_products(
    tenant_id: str = Query(..., description="Filter by tenant ID"),
    in_stock:  bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
):
    """List products for a tenant's catalog."""
    products = await get_products_for_tenant(tenant_id, in_stock_only=in_stock, limit=limit)
    return APIResponse(success=True, message=f"{len(products)} products", data=products)


@product_router.get("/search", response_model=APIResponse)
async def api_search_products(
    tenant_id: str = Query(...),
    q: str = Query(..., description="Search term"),
):
    """Search products by name, description, or tags."""
    products = await search_products(tenant_id, q)
    return APIResponse(success=True, message=f"{len(products)} results", data=products)
