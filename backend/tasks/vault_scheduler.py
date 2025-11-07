"""
Vault Scheduler - Auto-refresh AI vaults every 6 hours
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from backend.services.vault_ai_service import vault_ai_service
from backend.services.supabase_client import supabase
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


async def refresh_all_vaults():
    """
    Refresh all vaults - called by scheduler
    """
    try:
        logger.info("[VAULT-SCHEDULER] 🔄 Starting scheduled vault refresh...")
        start_time = datetime.now()
        
        # Get all vaults
        result = supabase.table("vaults").select("id, name").order("id").execute()
        vaults = [(v["id"], v["name"]) for v in result.data]
        
        if not vaults:
            logger.info("[VAULT-SCHEDULER] No vaults to refresh")
            return
        
        logger.info(f"[VAULT-SCHEDULER] Found {len(vaults)} vaults to refresh")
        
        # Refresh each vault
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for vault_id, vault_name in vaults:
            try:
                logger.info(f"[VAULT-SCHEDULER] Refreshing vault #{vault_id}: {vault_name}")
                
                result = await vault_ai_service.refresh_vault(vault_id)
                
                if result["updated"]:
                    updated_count += 1
                    logger.info(
                        f"[VAULT-SCHEDULER] ✅ Vault #{vault_id} updated | "
                        f"APY: {result['old_apy']:.2f}% → {result['new_apy']:.2f}% "
                        f"({'+' if result['apy_delta'] > 0 else ''}{result['apy_delta']:.2f}%)"
                    )
                else:
                    skipped_count += 1
                    logger.info(f"[VAULT-SCHEDULER] ℹ️ Vault #{vault_id} skipped | {result['reason']}")
                
                # Small delay between vaults to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                error_count += 1
                logger.error(f"[VAULT-SCHEDULER] ❌ Failed to refresh vault #{vault_id}: {e}")
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"[VAULT-SCHEDULER] ✅ Refresh complete | "
            f"Updated: {updated_count} | Skipped: {skipped_count} | Errors: {error_count} | "
            f"Time: {elapsed:.1f}s"
        )
        
    except Exception as e:
        logger.error(f"[VAULT-SCHEDULER] ❌ Refresh job failed: {e}")


def start_vault_scheduler():
    """
    Start the vault auto-refresh scheduler
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("[VAULT-SCHEDULER] Scheduler already running")
        return
    
    try:
        # Get update interval from env (default 6 hours)
        update_interval_hours = int(getattr(settings, "VAULT_UPDATE_INTERVAL_HOURS", 6))
        
        logger.info(f"[VAULT-SCHEDULER] 🚀 Starting vault scheduler | Interval: {update_interval_hours}h")
        
        # Create scheduler
        scheduler = AsyncIOScheduler()
        
        # Add job with interval trigger
        scheduler.add_job(
            refresh_all_vaults,
            trigger=IntervalTrigger(hours=update_interval_hours),
            id="vault_refresh",
            name="Refresh AI Vaults",
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        # Start scheduler
        scheduler.start()
        
        logger.info(f"[VAULT-SCHEDULER] ✅ Scheduler started | Next run in {update_interval_hours}h")
        
        # Run immediately on startup (optional)
        if getattr(settings, "VAULT_REFRESH_ON_STARTUP", False):
            logger.info("[VAULT-SCHEDULER] Running initial refresh on startup...")
            asyncio.create_task(refresh_all_vaults())
        
    except Exception as e:
        logger.error(f"[VAULT-SCHEDULER] ❌ Failed to start scheduler: {e}")


def stop_vault_scheduler():
    """
    Stop the vault scheduler
    """
    global scheduler
    
    if scheduler is None:
        logger.warning("[VAULT-SCHEDULER] Scheduler not running")
        return
    
    try:
        logger.info("[VAULT-SCHEDULER] 🛑 Stopping vault scheduler...")
        scheduler.shutdown()
        scheduler = None
        logger.info("[VAULT-SCHEDULER] ✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"[VAULT-SCHEDULER] ❌ Failed to stop scheduler: {e}")


async def manual_refresh_all():
    """
    Manually trigger refresh of all vaults (for testing)
    """
    logger.info("[VAULT-SCHEDULER] 🔧 Manual refresh triggered")
    await refresh_all_vaults()
