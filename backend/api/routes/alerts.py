"""
Market Alerts API Routes
Provides real-time DeFi market alerts with AI reactions
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import logging

from backend.services.alerts_service import alerts_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_market_alerts():
    """
    Get latest market alerts
    
    Returns:
        JSONResponse with 'alerts' key containing list of alert objects
        Each alert includes:
        - protocol: Protocol name
        - change: Percentage change
        - type: "APY" or "TVL"
        - message: Human-readable alert message
        - ai_reaction: AI-generated contextual reaction
        - severity: "high", "medium", or "low"
        - current_apy: Current APY value
        - tvl: Total Value Locked
        - timestamp: ISO timestamp
    """
    try:
        logger.info("[ALERTS-API] 📡 Fetching market alerts...")
        alerts = await alerts_service.fetch_market_alerts()
        logger.info(f"[ALERTS-API] ✅ Returning {len(alerts)} alerts")
        
        return JSONResponse(content={
            "alerts": alerts,
            "count": len(alerts),
            "last_updated": alerts[0]["timestamp"] if alerts else None
        })
    
    except Exception as e:
        logger.error(f"[ALERTS-API] ❌ Error fetching alerts: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch alerts: {str(e)}"}
        )


@router.get("/summary")
async def get_alerts_summary():
    """
    Get summary statistics of current alerts
    
    Returns:
        JSONResponse with summary statistics
    """
    try:
        alerts = await alerts_service.fetch_market_alerts()
        
        # Count by severity
        severity_counts = {
            "high": sum(1 for a in alerts if a["severity"] == "high"),
            "medium": sum(1 for a in alerts if a["severity"] == "medium"),
            "low": sum(1 for a in alerts if a["severity"] == "low")
        }
        
        # Count by type
        type_counts = {
            "APY": sum(1 for a in alerts if a["type"] == "APY"),
            "TVL": sum(1 for a in alerts if a["type"] == "TVL")
        }
        
        # Average change
        avg_change = sum(abs(a["change"]) for a in alerts) / len(alerts) if alerts else 0
        
        return JSONResponse(content={
            "total_alerts": len(alerts),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "average_change": round(avg_change, 2),
            "last_updated": alerts[0]["timestamp"] if alerts else None
        })
    
    except Exception as e:
        logger.error(f"[ALERTS-API] ❌ Error fetching summary: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch summary: {str(e)}"}
        )
