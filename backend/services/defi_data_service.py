"""
DeFi Data Service
Fetches real-time token prices from CoinGecko and APY data from DeFiLlama
"""

import logging
import aiohttp
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache for token data (5 minute TTL)
_token_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = timedelta(minutes=5)

# CoinGecko token ID mapping
COINGECKO_TOKEN_MAP = {
    "ETH": "ethereum",
    "WETH": "ethereum",
    "AAVE": "aave",
    "stETH": "lido-dao",
    "CRV": "curve-dao-token",
    "UNI": "uniswap",
    "COMP": "compound-governance-token",
    "DAI": "dai",
    "USDC": "usd-coin",
    "USDT": "tether",
    "LINK": "chainlink",
    "MKR": "maker",
    "SNX": "synthetix-network-token",
    "YFI": "yearn-finance",
    "SUSHI": "sushi",
    "BAL": "balancer",
    "1INCH": "1inch",
}

# Protocol to DeFiLlama mapping
PROTOCOL_MAP = {
    "Aave": "aave-v3",
    "Aave V3": "aave-v3",
    "Compound": "compound-v3",
    "Compound V3": "compound-v3",
    "Curve": "curve-dex",
    "Uniswap": "uniswap-v3",
    "Uniswap V3": "uniswap-v3",
    "Lido": "lido",
    "MakerDAO": "makerdao",
    "Yearn": "yearn-finance",
}


class DeFiDataService:
    """Service for fetching real-time DeFi data"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.defillama_base = "https://yields.llama.fi"
        logger.info("[DEFI-DATA] 📊 DeFi Data Service initialized")
    
    async def fetch_token_data(self, symbol: str, protocol_name: str = None) -> Dict[str, Any]:
        """
        Fetch token price and APY data
        
        Args:
            symbol: Token symbol (e.g., "AAVE", "ETH")
            protocol_name: Optional protocol name for APY lookup
            
        Returns:
            Dict with price, apy, protocol_name
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{protocol_name}"
            if cache_key in _token_cache:
                cached = _token_cache[cache_key]
                if datetime.utcnow() - cached["timestamp"] < _cache_ttl:
                    logger.info(f"[DEFI-DATA] 💾 Cache hit for {symbol}")
                    return cached["data"]
            
            logger.info(f"[DEFI-DATA] 🔍 Fetching data for {symbol} on {protocol_name}")
            
            # Fetch price from CoinGecko
            price = await self._fetch_coingecko_price(symbol)
            
            # Fetch APY from DeFiLlama
            apy = await self._fetch_defillama_apy(symbol, protocol_name)
            
            # Determine protocol name
            final_protocol = protocol_name or self._guess_protocol(symbol)
            
            result = {
                "price": price,
                "apy": apy,
                "protocol_name": final_protocol,
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Cache result
            _token_cache[cache_key] = {
                "data": result,
                "timestamp": datetime.utcnow()
            }
            
            logger.info(f"[DEFI-DATA] ✅ Fetched {symbol}: ${price:.2f}, APY: {apy:.2f}%")
            return result
            
        except Exception as e:
            logger.error(f"[DEFI-DATA] ❌ Error fetching token data for {symbol}: {e}")
            # Return defaults
            return {
                "price": 0,
                "apy": 0,
                "protocol_name": protocol_name or "Unknown",
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _fetch_coingecko_price(self, symbol: str) -> float:
        """Fetch token price from CoinGecko"""
        try:
            token_id = COINGECKO_TOKEN_MAP.get(symbol.upper())
            if not token_id:
                logger.warning(f"[DEFI-DATA] ⚠️ No CoinGecko mapping for {symbol}")
                return 0
            
            url = f"{self.coingecko_base}/simple/price"
            params = {
                "ids": token_id,
                "vs_currencies": "usd"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data.get(token_id, {}).get("usd", 0)
                        return float(price)
                    else:
                        logger.warning(f"[DEFI-DATA] ⚠️ CoinGecko API error: {response.status}")
                        return 0
                        
        except Exception as e:
            logger.error(f"[DEFI-DATA] ❌ CoinGecko fetch error: {e}")
            return 0
    
    async def _fetch_defillama_apy(self, symbol: str, protocol_name: str = None) -> float:
        """Fetch APY from DeFiLlama"""
        try:
            url = f"{self.defillama_base}/pools"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        pools = data.get("data", [])
                        
                        # Filter pools by symbol and protocol
                        matching_pools = []
                        for pool in pools:
                            pool_symbol = pool.get("symbol", "").upper()
                            pool_project = pool.get("project", "").lower()
                            
                            # Check if symbol matches
                            if symbol.upper() in pool_symbol:
                                # If protocol specified, match it
                                if protocol_name:
                                    protocol_key = PROTOCOL_MAP.get(protocol_name, protocol_name.lower())
                                    if protocol_key in pool_project:
                                        matching_pools.append(pool)
                                else:
                                    matching_pools.append(pool)
                        
                        # Return highest APY from matching pools
                        if matching_pools:
                            apys = [p.get("apy", 0) for p in matching_pools if p.get("apy")]
                            if apys:
                                return max(apys)
                        
                        # Fallback: return default APY based on protocol
                        return self._get_default_apy(protocol_name)
                    else:
                        logger.warning(f"[DEFI-DATA] ⚠️ DeFiLlama API error: {response.status}")
                        return self._get_default_apy(protocol_name)
                        
        except Exception as e:
            logger.error(f"[DEFI-DATA] ❌ DeFiLlama fetch error: {e}")
            return self._get_default_apy(protocol_name)
    
    def _get_default_apy(self, protocol_name: str = None) -> float:
        """Return default APY based on protocol"""
        defaults = {
            "Aave": 3.5,
            "Aave V3": 3.5,
            "Compound": 2.8,
            "Compound V3": 2.8,
            "Curve": 4.2,
            "Uniswap": 5.0,
            "Uniswap V3": 5.0,
            "Lido": 3.2,
            "MakerDAO": 1.5,
            "Yearn": 6.5,
        }
        return defaults.get(protocol_name, 3.0)
    
    def _guess_protocol(self, symbol: str) -> str:
        """Guess protocol based on token symbol"""
        if symbol.upper() in ["AAVE", "aAAVE", "aUSDC", "aDAI"]:
            return "Aave V3"
        elif symbol.upper() in ["COMP", "cUSDC", "cDAI"]:
            return "Compound V3"
        elif symbol.upper() in ["CRV", "3CRV"]:
            return "Curve"
        elif symbol.upper() in ["stETH", "wstETH"]:
            return "Lido"
        elif symbol.upper() in ["UNI"]:
            return "Uniswap V3"
        else:
            return "Unknown"


# Singleton instance
defi_data_service = DeFiDataService()
