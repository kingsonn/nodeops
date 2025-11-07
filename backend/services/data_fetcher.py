"""
Data Fetcher Service

Fetches and caches DeFi protocol data from DeFiLlama and CoinGecko APIs.
Stores normalized data in Supabase with TTL-based caching.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from cachetools import TTLCache
from supabase import create_client, Client

from backend.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics counters
metrics = {
    "defillama_fetch_total": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "coingecko_fetch_total": 0,
    "supabase_upserts": 0
}

# In-memory TTL cache (15 minutes default)
_cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL)
_cache_key = "protocol_data"

# Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured")
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("✓ Supabase client initialized")
    return _supabase_client


async def fetch_from_defillama() -> List[Dict[str, Any]]:
    """
    Fetch protocol data from DeFiLlama API
    
    Returns:
        List of raw pool data from DeFiLlama
    """
    metrics["defillama_fetch_total"] += 1
    logger.info(f"Fetching data from DeFiLlama: {settings.DEFI_LLAMA_URL}")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {}
            if settings.DEFILLAMA_API_KEY:
                headers["Authorization"] = f"Bearer {settings.DEFILLAMA_API_KEY}"
            
            async with session.get(settings.DEFI_LLAMA_URL, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"DeFiLlama API error: {response.status}")
                    print(f"[DEFI-LLAMA] API error: Status {response.status}")
                    return []
                
                data = await response.json()
                pools = data.get("data", []) if isinstance(data, dict) else data
                
                # Log raw API sample (first 2 items only)
                print(f"[DEFI-LLAMA] Raw API sample (first 2 pools): {pools[:2]}")
                
                logger.info(f"✓ Retrieved {len(pools)} pools from DeFiLlama")
                print(f"[DEFI-LLAMA] Total pools fetched: {len(pools)}")
                return pools
                
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching from DeFiLlama: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching from DeFiLlama: {e}")
        return []


async def fetch_from_coingecko() -> List[Dict[str, Any]]:
    """
    Fetch fallback data from CoinGecko API
    
    Returns:
        List of simplified protocol data from CoinGecko
    """
    metrics["coingecko_fetch_total"] += 1
    logger.info(f"Fetching fallback data from CoinGecko")
    
    try:
        url = f"{settings.COINGECKO_URL}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": "aave,lido-dao,curve-dao-token,uniswap,compound-governance-token",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": False
        }
        
        async with aiohttp.ClientSession() as session:
            headers = {}
            if settings.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY
            
            async with session.get(url, params=params, headers=headers, timeout=30) as response:
                if response.status != 200:
                    logger.error(f"CoinGecko API error: {response.status}")
                    print(f"[COINGECKO-FALLBACK] API error: Status {response.status}")
                    return []
                
                data = await response.json()
                
                # Log raw response (first 2 items only)
                print(f"[COINGECKO-FALLBACK] Raw response sample: {data[:2]}")
                
                logger.info(f"✓ Retrieved {len(data)} tokens from CoinGecko")
                print(f"[COINGECKO-FALLBACK] Total tokens fetched: {len(data)}")
                return data
                
    except Exception as e:
        logger.error(f"Error fetching from CoinGecko: {e}")
        return []


def normalize_defillama_data(raw_pools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize DeFiLlama pool data to standard format
    
    Args:
        raw_pools: Raw pool data from DeFiLlama
        
    Returns:
        List of normalized protocol data
    """
    normalized = []
    
    for pool in raw_pools:
        try:
            tvl_usd = float(pool.get("tvlUsd", 0))
            apy = float(pool.get("apy", 0))
            
            # Determine risk level based on TVL
            if tvl_usd > 1_000_000:
                risk = "low"
            elif tvl_usd > 100_000:
                risk = "medium"
            else:
                risk = "high"
            
            normalized_pool = {
                "id": pool.get("project", "unknown"),
                "chain": pool.get("chain", "unknown"),
                "apy": round(apy, 2),
                "tvl_usd": round(tvl_usd, 2),
                "metadata": {
                    "symbol": pool.get("symbol", ""),
                    "url": pool.get("url", ""),
                    "category": pool.get("category", ""),
                    "pool_id": pool.get("pool", "")
                },
                "risk": risk,
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            normalized.append(normalized_pool)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error normalizing pool {pool.get('project', 'unknown')}: {e}")
            continue
    
    logger.info(f"✓ Normalized {len(normalized)} protocols")
    return normalized


def normalize_coingecko_data(raw_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize CoinGecko token data to standard format
    
    Args:
        raw_tokens: Raw token data from CoinGecko
        
    Returns:
        List of normalized protocol data
    """
    normalized = []
    
    # Map CoinGecko IDs to protocol names
    id_map = {
        "aave": "Aave",
        "lido-dao": "Lido",
        "curve-dao-token": "Curve",
        "uniswap": "Uniswap",
        "compound-governance-token": "Compound"
    }
    
    for token in raw_tokens:
        try:
            token_id = token.get("id", "")
            protocol_name = id_map.get(token_id, token.get("name", "Unknown"))
            
            market_cap = float(token.get("market_cap", 0))
            
            # Estimate APY (placeholder - CoinGecko doesn't provide APY)
            apy = 3.5  # Default placeholder
            
            normalized_token = {
                "id": protocol_name.lower(),
                "chain": "ethereum",
                "apy": apy,
                "tvl_usd": round(market_cap / 10, 2),  # Rough estimate
                "metadata": {
                    "symbol": token.get("symbol", "").upper(),
                    "url": f"https://www.coingecko.com/en/coins/{token_id}",
                    "category": "defi",
                    "price_usd": token.get("current_price", 0)
                },
                "risk": "medium",
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            normalized.append(normalized_token)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error normalizing token {token.get('id', 'unknown')}: {e}")
            continue
    
    logger.info(f"✓ Normalized {len(normalized)} protocols from CoinGecko")
    return normalized


async def save_to_supabase(protocols: List[Dict[str, Any]]) -> int:
    """
    Upsert normalized protocol data to Supabase
    
    Args:
        protocols: List of normalized protocol data
        
    Returns:
        Number of records upserted
    """
    if not protocols:
        logger.warning("No protocols to save")
        return 0
    
    try:
        client = get_supabase_client()
        
        # Prepare data for upsert
        records = []
        for protocol in protocols:
            record = {
                "protocol_name": protocol["id"],
                "chain": protocol["chain"],
                "apy": protocol["apy"],
                "tvl": protocol["tvl_usd"],
                "category": protocol["metadata"].get("category", "defi"),
                "data": protocol["metadata"],
                "fetched_at": protocol["fetched_at"]
            }
            records.append(record)
        
        # Upsert in batches of 100
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            response = client.table("protocol_data").upsert(
                batch,
                on_conflict="protocol_name"
            ).execute()
            
            total_upserted += len(batch)
            metrics["supabase_upserts"] += len(batch)
        
        logger.info(f"✓ Upserted {total_upserted} records to Supabase")
        return total_upserted
        
    except Exception as e:
        logger.error(f"Error saving to Supabase: {e}")
        return 0


async def refresh_data() -> List[Dict[str, Any]]:
    """
    Fetch fresh data from APIs, normalize, and save to Supabase
    
    Returns:
        List of normalized protocol data
    """
    logger.info("Starting data refresh...")
    
    # Try DeFiLlama first
    raw_pools = await fetch_from_defillama()
    
    if raw_pools:
        protocols = normalize_defillama_data(raw_pools)
    else:
        # Fallback to CoinGecko
        logger.warning("DeFiLlama failed, using CoinGecko fallback")
        raw_tokens = await fetch_from_coingecko()
        protocols = normalize_coingecko_data(raw_tokens)
    
    # Save to Supabase
    if protocols:
        await save_to_supabase(protocols)
        
        # Update cache
        _cache[_cache_key] = {
            "timestamp": time.time(),
            "data": protocols
        }
        logger.info(f"✓ Cache updated with {len(protocols)} protocols")
    
    return protocols


async def get_cached_data(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Get cached protocol data or refresh if stale
    
    Args:
        force_refresh: If True, bypass cache and fetch fresh data
        
    Returns:
        Dictionary with timestamp and protocol data
    """
    # Check cache first
    if not force_refresh and _cache_key in _cache:
        metrics["cache_hits"] += 1
        cached = _cache[_cache_key]
        logger.info(f"✓ Cache hit - returning {len(cached['data'])} protocols")
        return cached
    
    # Cache miss - fetch fresh data
    metrics["cache_misses"] += 1
    logger.info("Cache miss - fetching fresh data")
    
    protocols = await refresh_data()
    
    return {
        "timestamp": time.time(),
        "data": protocols
    }


def get_metrics() -> Dict[str, int]:
    """Get current metrics"""
    return metrics.copy()
