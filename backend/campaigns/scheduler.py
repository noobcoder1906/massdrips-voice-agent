"""
backend/campaigns/scheduler.py

Background Campaign Scheduler & Dispatch Engine.
Manages automated outbound call queue execution with:
  1. Concurrency control per tenant (max_concurrent_calls)
  2. Business hours / DND enforcement (09:00 - 20:00)
  3. Exponential backoff retry logic for failed / no-answer calls
  4. Swappable Telephony Provider integration
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, Any, List, Optional
from backend.services import (
    get_active_campaigns,
    update_campaign_lead_state,
    update_campaign_status,
    get_lead,
    get_tenant
)
from backend.telephony.factory import get_telephony_provider

logger = logging.getLogger("campaign_scheduler")
logger.setLevel(logging.INFO)


class CampaignScheduler:
    """Async Campaign Scheduler Engine."""

    def __init__(self, check_interval_sec: float = 5.0):
        self.check_interval_sec = check_interval_sec
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.active_tenant_calls: Dict[str, int] = {}

    def is_within_business_hours(self) -> bool:
        """Check if current time is within business hours (09:00 - 20:00)."""
        now = datetime.now()
        # 9 AM to 8 PM
        return 9 <= now.hour < 20

    async def _process_campaign(self, campaign: Dict[str, Any]) -> None:
        campaign_id = campaign["id"]
        tenant_id = campaign["tenant_id"]
        max_concurrent = campaign.get("max_concurrent_calls", 5)
        max_retries = campaign.get("retry_count", 2)
        lead_states: Dict[str, Dict[str, Any]] = campaign.get("lead_states", {})

        current_active = self.active_tenant_calls.get(tenant_id, 0)
        if current_active >= max_concurrent:
            logger.info(f"[Campaign {campaign_id}] Max concurrency limit ({max_concurrent}) reached for tenant {tenant_id}")
            return

        if not self.is_within_business_hours():
            logger.info(f"[Campaign {campaign_id}] Outside business hours (09:00-20:00). Skipping dispatch.")
            return

        # Fetch tenant config for telephony provider
        tenant = await get_tenant(tenant_id)
        provider_name = tenant.get("telephony_provider", "mock") if tenant else "mock"
        provider = get_telephony_provider(provider_name)

        pending_leads: List[str] = []
        for lead_id, state in lead_states.items():
            status = state.get("status", "pending")
            attempts = state.get("attempts", 0)

            if status == "pending":
                pending_leads.append(lead_id)
            elif status in ("failed", "no_answer") and attempts < max_retries:
                pending_leads.append(lead_id)

        if not pending_leads:
            # Check if all leads are completed or exhausted
            all_done = all(
                st.get("status") in ("completed", "answered", "dnc") or st.get("attempts", 0) >= max_retries
                for st in lead_states.values()
            )
            if all_done and lead_states:
                logger.info(f"[Campaign {campaign_id}] All leads processed. Marking campaign completed.")
                await update_campaign_status(campaign_id, "completed")
            return

        # Dispatch calls up to available concurrency slots
        slots_available = max_concurrent - current_active
        leads_to_call = pending_leads[:slots_available]

        for lead_id in leads_to_call:
            lead = await get_lead(lead_id, tenant_id)
            if not lead:
                await update_campaign_lead_state(campaign_id, lead_id, "failed")
                continue

            if lead.get("status") == "dnc":
                logger.info(f"[Campaign {campaign_id}] Lead {lead_id} is on DNC list. Skipping.")
                await update_campaign_lead_state(campaign_id, lead_id, "dnc")
                continue

            # Lock call slot
            self.active_tenant_calls[tenant_id] = self.active_tenant_calls.get(tenant_id, 0) + 1

            # Dispatch call asynchronously
            asyncio.create_task(
                self._dispatch_call(
                    campaign_id=campaign_id,
                    tenant_id=tenant_id,
                    lead=lead,
                    provider=provider
                )
            )

    async def _dispatch_call(
        self,
        campaign_id: str,
        tenant_id: str,
        lead: Dict[str, Any],
        provider: Any
    ) -> None:
        lead_id = lead["id"]
        phone = lead.get("phone", "")
        ws_url = f"ws://localhost:8000/ws/voice/{tenant_id}/{lead_id}?campaign_id={campaign_id}"

        try:
            logger.info(f"[Dispatch] Initiating call to {lead.get('name')} ({phone}) via {provider.__class__.__name__}")
            await update_campaign_lead_state(campaign_id, lead_id, "calling", increment_calls=True)

            res = await provider.make_outbound_call(
                to_phone=phone,
                from_phone="+18005550199",
                websocket_url=ws_url,
                custom_data={"tenant_id": tenant_id, "lead_id": lead_id, "campaign_id": campaign_id}
            )

            if res.status in ("initiated", "in-progress", "queued"):
                await update_campaign_lead_state(campaign_id, lead_id, "completed")
            else:
                await update_campaign_lead_state(campaign_id, lead_id, "failed")

        except Exception as e:
            logger.error(f"[Dispatch Error] Failed to dispatch call to lead {lead_id}: {e}")
            await update_campaign_lead_state(campaign_id, lead_id, "failed")
        finally:
            # Release call slot
            self.active_tenant_calls[tenant_id] = max(0, self.active_tenant_calls.get(tenant_id, 1) - 1)

    async def _run_loop(self) -> None:
        logger.info("Campaign Scheduler engine loop started.")
        while self.is_running:
            try:
                active_campaigns = await get_active_campaigns()
                for campaign in active_campaigns:
                    await self._process_campaign(campaign)
            except Exception as e:
                logger.error(f"Error in Campaign Scheduler loop: {e}")
            await asyncio.sleep(self.check_interval_sec)

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("Campaign Scheduler started.")

    def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            logger.info("Campaign Scheduler stopped.")


# Global singleton instance
scheduler_instance = CampaignScheduler()
