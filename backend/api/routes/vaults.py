"""
Vaults API Routes - AI-powered DeFi vault management
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.services.vault_ai_service import vault_ai_service
from backend.services.supabase_client import supabase
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vaults", tags=["vaults"])


# ============================================
# Request/Response Models
# ============================================

class GenerateVaultRequest(BaseModel):
    risk_preference: str = Field(..., pattern="^(low|medium|high)$")


class SimulateVaultRequest(BaseModel):
    wallet: str
    vault_id: int
    deposit_amount: float
    subscribe: bool = False


class VaultResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    risk_level: str
    expected_apy: float
    allocations: List[dict]
    last_updated: str
    ai_description: Optional[str]
    created_at: str


class VaultLogResponse(BaseModel):
    id: int
    vault_id: int
    event_type: str
    summary: str
    confidence: Optional[float]
    ai_model: Optional[str]
    created_at: str


# ============================================
# Endpoints
# ============================================

@router.get("/", response_model=List[VaultResponse])
async def list_vaults():
    """
    List all AI vaults
    """
    try:
        result = supabase.table("vaults").select("*").order("last_updated", desc=True).execute()
        
        vaults = []
        for vault in result.data:
            vaults.append({
                "id": vault["id"],
                "name": vault["name"],
                "description": vault.get("description", ""),
                "risk_level": vault["risk_level"],
                "expected_apy": float(vault["expected_apy"]) if vault.get("expected_apy") else 0.0,
                "allocations": vault.get("allocations", []),
                "last_updated": vault.get("last_updated", ""),
                "ai_description": vault.get("ai_description", ""),
                "created_at": vault.get("created_at", "")
            })
        
        logger.info(f"[VAULTS-API] Listed {len(vaults)} vaults")
        return vaults
        
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to list vaults: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vault_id}")
async def get_vault(vault_id: int):
    """
    Get detailed vault information with recent logs
    """
    try:
        # Get vault
        vault_result = supabase.table("vaults").select("*").eq("id", vault_id).execute()
        
        if not vault_result.data:
            raise HTTPException(status_code=404, detail=f"Vault {vault_id} not found")
        
        vault = vault_result.data[0]
        
        # Get recent logs
        logs_result = supabase.table("vault_ai_logs").select("*").eq("vault_id", vault_id).order("created_at", desc=True).limit(5).execute()
        
        logs = []
        for log in logs_result.data:
            logs.append({
                "id": log["id"],
                "vault_id": log["vault_id"],
                "event_type": log["event_type"],
                "summary": log["summary"],
                "confidence": float(log["confidence"]) if log.get("confidence") else None,
                "ai_model": log.get("ai_model"),
                "created_at": log.get("created_at", "")
            })
        
        vault["recent_logs"] = logs
        
        logger.info(f"[VAULTS-API] Retrieved vault #{vault_id} with {len(logs)} logs")
        return vault
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to get vault {vault_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_vault(request: GenerateVaultRequest):
    """
    Generate a new AI vault based on risk preference
    Rate-limited endpoint
    """
    try:
        logger.info(f"[VAULTS-API] Generating vault | Risk: {request.risk_preference}")
        
        # Generate vault using AI service
        vault_data = await vault_ai_service.generate_ai_vault(
            risk_preference=request.risk_preference
        )
        
        logger.info(f"[VAULTS-API] ✅ Generated vault #{vault_data['id']}")
        return vault_data
        
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to generate vault: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate_vault_deposit(request: SimulateVaultRequest):
    """
    Simulate depositing into a vault and calculate expected returns
    Optionally subscribe (save to vault_subscriptions)
    """
    try:
        logger.info(f"[VAULTS-API] Simulating deposit | Vault: {request.vault_id} | Amount: ${request.deposit_amount}")
        
        # Get vault
        vault_result = supabase.table("vaults").select("expected_apy, allocations").eq("id", request.vault_id).execute()
        
        if not vault_result.data:
            raise HTTPException(status_code=404, detail=f"Vault {request.vault_id} not found")
        
        vault = vault_result.data[0]
        vault_apy = float(vault["expected_apy"]) if vault.get("expected_apy") else 0.0
        allocations = vault.get("allocations", [])
        
        # Calculate expected annual gain
        expected_gain_usd = (request.deposit_amount * vault_apy) / 100
        
        # Simulate allocation breakdown
        simulated_allocation = []
        for alloc in allocations:
            amount = (request.deposit_amount * alloc["percent"]) / 100
            simulated_allocation.append({
                "protocol_name": alloc["protocol_name"],
                "percent": alloc["percent"],
                "amount_usd": round(amount, 2)
            })
        
        simulation_result = {
            "vault_id": request.vault_id,
            "deposit_amount": request.deposit_amount,
            "vault_apy": vault_apy,
            "expected_gain_usd": round(expected_gain_usd, 2),
            "simulated_allocation": simulated_allocation
        }
        
        # If subscribe, save to DB
        if request.subscribe:
            sub_result = supabase.table("vault_subscriptions").insert({
                "vault_id": request.vault_id,
                "deposit_amount": request.deposit_amount
            }).execute()
            
            subscription_id = sub_result.data[0]["id"]
            
            simulation_result["subscribed"] = True
            simulation_result["subscription_id"] = subscription_id
            logger.info(f"[VAULTS-API] ✅ Subscribed to vault #{request.vault_id} | Sub ID: {subscription_id}")
        
        return simulation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to simulate deposit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{vault_id}/refresh")
async def refresh_vault(vault_id: int):
    """
    Manually trigger vault refresh (re-evaluation)
    Useful for demo to force immediate update
    """
    try:
        logger.info(f"[VAULTS-API] Manual refresh triggered | Vault: {vault_id}")
        
        # Refresh vault using AI service
        result = await vault_ai_service.refresh_vault(vault_id)
        
        if result["updated"]:
            logger.info(f"[VAULTS-API] ✅ Vault #{vault_id} updated | APY: {result['old_apy']:.2f}% → {result['new_apy']:.2f}%")
        else:
            logger.info(f"[VAULTS-API] ℹ️ Vault #{vault_id} not updated | {result['reason']}")
        
        return result
        
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to refresh vault {vault_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{vault_id}/logs", response_model=List[VaultLogResponse])
async def get_vault_logs(vault_id: int, limit: int = 10):
    """
    Get AI decision logs for a vault
    """
    try:
        result = supabase.table("vault_ai_logs").select("*").eq("vault_id", vault_id).order("created_at", desc=True).limit(limit).execute()
        
        logs = []
        for log in result.data:
            logs.append({
                "id": log["id"],
                "vault_id": log["vault_id"],
                "event_type": log["event_type"],
                "summary": log["summary"],
                "confidence": float(log["confidence"]) if log.get("confidence") else None,
                "ai_model": log.get("ai_model"),
                "created_at": log.get("created_at", "")
            })
        
        logger.info(f"[VAULTS-API] Retrieved {len(logs)} logs for vault #{vault_id}")
        return logs
        
    except Exception as e:
        logger.error(f"[VAULTS-API] Failed to get logs for vault {vault_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
