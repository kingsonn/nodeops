"""
Market Alerts Service
Fetches and generates DeFi market alerts from live data sources
"""

import aiohttp
import random
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AlertsService:
    """Service for fetching and generating market alerts"""
    
    def __init__(self):
        self.cache = []
        self.last_fetch = None
        self.cache_duration = 120  # 2 minutes in seconds
    
    async def fetch_market_alerts(self) -> List[Dict[str, Any]]:
        """
        Fetch latest market alerts from DeFiLlama and generate AI reactions
        Returns list of alert objects with protocol, change, type, message, AI reaction
        """
        try:
            # Check cache first
            if self.cache and self.last_fetch:
                elapsed = (datetime.utcnow() - self.last_fetch).total_seconds()
                if elapsed < self.cache_duration:
                    logger.info(f"[ALERTS] 📦 Returning cached alerts ({len(self.cache)} items)")
                    return self.cache
            
            logger.info("[ALERTS] 🌐 Fetching fresh market data from DeFiLlama...")
            
            # Fetch from DeFiLlama
            async with aiohttp.ClientSession() as session:
                async with session.get("https://yields.llama.fi/pools", timeout=10) as response:
                    data = await response.json()
                    pools = data.get("data", [])[:100]  # Top 100 pools
            
            if not pools:
                logger.warning("[ALERTS] ⚠️ No pools data received")
                return self.cache or []
            
            # Generate alerts from random sample
            alerts = []
            sample_size = min(8, len(pools))  # 8 alerts per fetch
            sampled_pools = random.sample(pools, sample_size)
            
            for pool in sampled_pools:
                protocol = pool.get("project", "Unknown")
                current_apy = pool.get("apy", 0)
                tvl = pool.get("tvlUsd", 0)
                
                # Simulate change (in production, compare with historical data)
                change = round(random.uniform(-2.5, 3.5), 2)
                change_type = random.choice(["APY", "TVL"]) if abs(change) > 0.5 else "TVL"
                
                # Determine alert severity
                severity = self._get_severity(change)
                
                # Generate message
                direction = "increased" if change > 0 else "decreased"
                message = f"{protocol.capitalize()} {change_type} {direction} by {abs(change)}%"
                
                # Generate AI reaction based on change magnitude and type
                ai_reaction = self._generate_ai_reaction(change, change_type, protocol, current_apy)
                
                alerts.append({
                    "protocol": protocol,
                    "change": change,
                    "type": change_type,
                    "message": message,
                    "ai_reaction": ai_reaction,
                    "severity": severity,
                    "current_apy": round(current_apy, 2),
                    "tvl": tvl,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
            # Sort by severity (high → medium → low) and timestamp
            alerts.sort(key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x["severity"]],
                x["timestamp"]
            ), reverse=True)
            
            # Update cache
            self.cache = alerts
            self.last_fetch = datetime.utcnow()
            
            logger.info(f"[ALERTS] ✅ Generated {len(alerts)} market alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"[ALERTS] ❌ Failed to fetch alerts: {e}")
            return self.cache or []
    
    def _get_severity(self, change: float) -> str:
        """Determine alert severity based on change magnitude"""
        abs_change = abs(change)
        if abs_change >= 2.0:
            return "high"
        elif abs_change >= 1.0:
            return "medium"
        else:
            return "low"
    
    def _generate_ai_reaction(self, change: float, change_type: str, protocol: str, apy: float) -> str:
        """Generate contextual AI reaction based on market change"""
        abs_change = abs(change)
        
        # High impact changes (>2%)
        if abs_change >= 2.0:
            if change > 0:
                reactions = [
                    f"Significant yield opportunity detected. {protocol} showing strong momentum.",
                    f"Major APY increase may attract liquidity. Consider rebalancing exposure.",
                    f"Substantial yield shift. AI recommends monitoring {protocol} closely.",
                    f"High-impact event. This could affect portfolio allocation strategies."
                ]
            else:
                reactions = [
                    f"Sharp decline detected. AI suggests reviewing {protocol} positions.",
                    f"Significant yield compression. May indicate market stress or competition.",
                    f"Major downward movement. Consider defensive positioning.",
                    f"High-impact drop. AI recommends caution with {protocol} exposure."
                ]
        
        # Medium impact changes (1-2%)
        elif abs_change >= 1.0:
            if change > 0:
                reactions = [
                    f"Moderate yield increase. {protocol} remains competitive in current market.",
                    f"Positive momentum detected. AI sees potential for continued growth.",
                    f"Yield improvement noted. May present tactical opportunity.",
                    f"Upward trend emerging. Worth monitoring for portfolio inclusion."
                ]
            else:
                reactions = [
                    f"Moderate yield decline. {protocol} still within normal volatility range.",
                    f"Minor compression detected. AI assesses as temporary market adjustment.",
                    f"Slight downward pressure. No immediate action required.",
                    f"Yield normalization in progress. Expected market behavior."
                ]
        
        # Low impact changes (<1%)
        else:
            reactions = [
                f"Minor fluctuation. {protocol} yields remain stable overall.",
                f"Negligible change. AI sees no material impact on portfolio strategy.",
                f"Normal market noise. {protocol} performing as expected.",
                f"Minimal variance. No significant implications for current allocations.",
                f"Stable conditions. AI confidence in {protocol} unchanged."
            ]
        
        return random.choice(reactions)


# Singleton instance
alerts_service = AlertsService()
