"""
Data Routes

API endpoints for fetching DeFi protocol data from DeFiLlama and CoinGecko.
Includes caching, rate limiting, and filtering capabilities.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Request, Query, HTTPException

from backend.services.data_fetcher import get_cached_data, get_metrics
from backend.core.security import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/")
async def get_protocol_data(
    request: Request,
    fresh: bool = Query(False, description="Force refresh data from APIs"),
    protocols: Optional[str] = Query(None, description="Comma-separated list of protocol IDs to filter"),
    include_metadata: bool = Query(False, description="Include full metadata in response")
):
    """
    Get DeFi protocol data with caching and filtering
    
    Query Parameters:
    - fresh: If true, bypass cache and fetch fresh data
    - protocols: Filter by specific protocol IDs (e.g., "aave,lido")
    - include_metadata: Include detailed metadata fields
    
    Returns:
        JSON response with timestamp and protocol data
    """
    # Rate limiting
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    # Get data (cached or fresh)
    try:
        cached_result = await get_cached_data(force_refresh=fresh)
        protocols_data = cached_result.get("data", [])
        timestamp = cached_result.get("timestamp", 0)
        
        # Filter by protocols if specified
        if protocols:
            protocol_list = [p.strip().lower() for p in protocols.split(",")]
            protocols_data = [
                p for p in protocols_data 
                if p.get("id", "").lower() in protocol_list
            ]
            logger.info(f"Filtered to {len(protocols_data)} protocols: {protocol_list}")
        
        # Remove metadata if not requested
        if not include_metadata:
            protocols_data = [
                {
                    "id": p["id"],
                    "chain": p["chain"],
                    "apy": p["apy"],
                    "tvl_usd": p["tvl_usd"],
                    "risk": p["risk"]
                }
                for p in protocols_data
            ]
        
        return {
            "timestamp": int(timestamp),
            "count": len(protocols_data),
            "protocols": protocols_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching protocol data: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch protocol data", "message": str(e)}
        )


@router.get("/metrics")
async def get_data_metrics(request: Request):
    """
    Get metrics for data fetcher service
    
    Returns:
        Prometheus-style metrics
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    metrics = get_metrics()
    return {
        "metrics": metrics,
        "description": {
            "defillama_fetch_total": "Total DeFiLlama API calls",
            "coingecko_fetch_total": "Total CoinGecko API calls",
            "cache_hits": "Number of cache hits",
            "cache_misses": "Number of cache misses",
            "supabase_upserts": "Total records upserted to Supabase"
        }
    }
