"""
AI Vault Service - Autonomous DeFi Vault Generation and Management
Powered by Groq LLaMA 3.3 70B
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from groq import Groq
from backend.core.config import settings
from backend.services.supabase_client import supabase

logger = logging.getLogger(__name__)

class VaultAIService:
    """Service for AI-powered vault generation and management"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.groq_client = None
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("✅ Groq client initialized for Vault AI")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq client: {e}")
        else:
            logger.warning("⚠️ GROQ_API_KEY not set - AI vault generation will use fallback")
    
    async def generate_ai_vault(
        self,
        risk_preference: str = "medium",
        protocols: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new AI vault strategy based on live DeFi data
        
        Args:
            risk_preference: "low", "medium", or "high"
            protocols: Optional pre-fetched protocol data
            
        Returns:
            Dict with vault data including allocations and metadata
        """
        try:
            logger.info(f"[VAULT-AI] 🧠 Generating new AI vault | Risk: {risk_preference}")
            start_time = time.time()
            
            # 1. Fetch live protocol data if not provided
            if not protocols:
                protocols = await self._fetch_protocol_data()
            
            logger.info(f"[VAULT-AI] 📊 Loaded {len(protocols)} protocols for analysis")
            
            # 2. Call Groq AI to generate vault strategy
            vault_data = await self._call_groq_for_generation(risk_preference, protocols)
            
            # 3. Validate and compute expected APY
            vault_data = self._validate_and_compute_apy(vault_data, protocols)
            
            # 4. Save to database
            vault_id = await self._save_vault_to_db(vault_data)
            vault_data["id"] = vault_id
            
            # 5. Log AI decision
            await self._log_vault_event(
                vault_id=vault_id,
                event_type="generate",
                payload=vault_data,
                summary=f"Generated new vault: {vault_data['name']} | APY: {vault_data['expected_apy']:.2f}%",
                confidence=vault_data.get("confidence", 0.85),
                ai_model=settings.AI_MODEL
            )
            
            elapsed = time.time() - start_time
            
            # Detailed console output for demo/debugging
            logger.info(f"[VAULT-AI] ✅ Generated vault '{vault_data['name']}'")
            
            # Format allocations
            alloc_str = ', '.join([f"{a['protocol_name']} ({a['percent']}%)" for a in vault_data.get('allocations', [])])
            logger.info(f"[VAULT-AI] Allocations: {alloc_str}")
            logger.info(f"[VAULT-AI] Weighted APY: {vault_data['expected_apy']:.2f}%")
            
            reasoning = vault_data.get('notes', 'N/A')[:150]
            logger.info(f"[VAULT-AI] Reasoning: {reasoning}...")
            logger.info(f"[VAULT-AI] Time: {elapsed:.2f}s")
            
            return vault_data
            
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to generate vault: {e}")
            raise
    
    async def refresh_vault(self, vault_id: int) -> Dict[str, Any]:
        """
        Re-evaluate and update an existing vault based on latest market data
        
        Args:
            vault_id: ID of vault to refresh
            
        Returns:
            Dict with update summary and new vault data
        """
        try:
            logger.info(f"[VAULT-AI] 🔄 Refreshing vault #{vault_id}")
            start_time = time.time()
            
            # 1. Fetch vault from DB
            vault = await self._get_vault_from_db(vault_id)
            if not vault:
                raise ValueError(f"Vault #{vault_id} not found")
            
            old_apy = float(vault.get("expected_apy", 0))
            old_allocations = vault.get("allocations", [])
            
            # 2. Fetch latest protocol data
            protocols = await self._fetch_protocol_data()
            
            # 3. Call Groq AI to re-evaluate
            update_data = await self._call_groq_for_refresh(
                vault=vault,
                protocols=protocols
            )
            
            # 4. Check if update is needed
            if update_data.get("action") == "no_change":
                logger.info(f"[VAULT-AI] ℹ️ Vault #{vault_id} | No update needed | {update_data.get('reason', '')}")
                await self._log_vault_event(
                    vault_id=vault_id,
                    event_type="update",
                    payload=update_data,
                    summary=f"No change: {update_data.get('reason', 'Current allocation optimal')}",
                    confidence=update_data.get("confidence", 0.0),
                    ai_model=settings.AI_MODEL
                )
                return {
                    "updated": False,
                    "reason": update_data.get("reason"),
                    "vault": vault
                }
            
            # 5. Validate update threshold
            new_apy = update_data.get("expected_apy", old_apy)
            apy_delta = abs(new_apy - old_apy)
            
            # Check if change is significant (≥0.5% APY or ≥10% allocation change)
            allocation_changed = self._check_allocation_change(old_allocations, update_data.get("new_allocations", []))
            
            if apy_delta < 0.5 and not allocation_changed:
                logger.info(f"[VAULT-AI] ℹ️ Vault #{vault_id} | Change too small | APY Δ: {apy_delta:.2f}%")
                return {
                    "updated": False,
                    "reason": "Change below threshold",
                    "vault": vault
                }
            
            # 6. Update vault in DB
            updated_vault = await self._update_vault_in_db(
                vault_id=vault_id,
                allocations=update_data["new_allocations"],
                expected_apy=new_apy,
                ai_description=update_data.get("reason", "")
            )
            
            # 7. Log update
            summary = f"APY {old_apy:.2f}% → {new_apy:.2f}% ({'+' if new_apy > old_apy else ''}{new_apy - old_apy:.2f}%) | {update_data.get('reason', '')}"
            await self._log_vault_event(
                vault_id=vault_id,
                event_type="update",
                payload=update_data,
                summary=summary,
                confidence=update_data.get("confidence", 0.0),
                ai_model=settings.AI_MODEL
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"[VAULT-AI] ✅ Updated vault #{vault_id} | {summary} | Time: {elapsed:.2f}s"
            )
            
            return {
                "updated": True,
                "old_apy": old_apy,
                "new_apy": new_apy,
                "apy_delta": new_apy - old_apy,
                "reason": update_data.get("reason"),
                "vault": updated_vault
            }
            
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to refresh vault #{vault_id}: {e}")
            # Log error
            await self._log_vault_event(
                vault_id=vault_id,
                event_type="error",
                payload={"error": str(e)},
                summary=f"Refresh failed: {str(e)}",
                confidence=0.0,
                ai_model=settings.AI_MODEL
            )
            raise
    
    async def _fetch_protocol_data(self) -> List[Dict]:
        """Fetch top protocols from DeFiLlama with live yield data"""
        try:
            import aiohttp
            
            logger.info("[VAULT-AI] 🌐 Fetching live DeFiLlama protocols...")
            
            # Fetch from DeFiLlama yields API
            async with aiohttp.ClientSession() as session:
                # Get pools with APY data
                async with session.get("https://yields.llama.fi/pools", timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"[VAULT-AI] DeFiLlama API error: {response.status}")
                        return await self._fetch_fallback_protocols()
                    
                    data = await response.json()
                    pools = data.get("data", [])
                    
                    logger.info(f"[VAULT-AI] ✅ Loaded {len(pools)} pools from DeFiLlama")
                    
                    # Filter and normalize pools
                    normalized_protocols = []
                    for pool in pools:
                        # Skip pools with no APY or very low TVL
                        if not pool.get("apy") or pool.get("tvlUsd", 0) < 1000000:
                            continue
                        
                        normalized_protocols.append({
                            "name": pool.get("project", "Unknown"),
                            "protocol_name": pool.get("project", "unknown").lower().replace(" ", "-"),
                            "apy": round(float(pool.get("apy", 0)), 2),
                            "tvl": pool.get("tvlUsd", 0),
                            "chain": pool.get("chain", "Unknown"),
                            "symbol": pool.get("symbol", ""),
                            "category": pool.get("category", "Unknown"),
                            "pool_id": pool.get("pool", "")
                        })
                    
                    # Sort by TVL and take top 200
                    normalized_protocols.sort(key=lambda x: x.get("tvl", 0), reverse=True)
                    top_protocols = normalized_protocols[:200]
                    
                    logger.info(f"[VAULT-AI] ✅ Filtered to {len(top_protocols)} protocols with TVL > $1M")
                    
                    # Fetch token prices from CoinGecko
                    await self._enrich_with_prices(top_protocols)
                    
                    return top_protocols
            
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to fetch protocol data: {e}")
            return await self._fetch_fallback_protocols()
    
    async def _enrich_with_prices(self, protocols: List[Dict]):
        """Enrich protocols with live token prices from CoinGecko"""
        try:
            import aiohttp
            
            logger.info("[VAULT-AI] 🌐 Fetching live prices from CoinGecko...")
            
            # Get unique token IDs
            token_ids = ["ethereum", "uniswap", "aave", "curve-dao-token", "lido-dao", 
                        "compound-governance-token", "balancer", "convex-finance", 
                        "yearn-finance", "maker", "frax-share"]
            
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(token_ids)}&vs_currencies=usd"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        prices = await response.json()
                        logger.info(f"[VAULT-AI] ✅ Prices loaded for {len(prices)} tokens")
                        
                        # Store prices for reference
                        for protocol in protocols:
                            protocol["price_data"] = prices
                    else:
                        logger.warning(f"[VAULT-AI] ⚠️ CoinGecko API error: {response.status}")
        
        except Exception as e:
            logger.warning(f"[VAULT-AI] ⚠️ Failed to fetch prices: {e}")
    
    async def _fetch_fallback_protocols(self) -> List[Dict]:
        """Fallback protocol data if APIs fail"""
        logger.warning("[VAULT-AI] ⚠️ Using fallback protocol data")
        return [
            {"name": "Lido", "protocol_name": "lido", "apy": 3.2, "tvl": 32000000000, "chain": "Ethereum", "category": "Liquid Staking"},
            {"name": "Aave V3", "protocol_name": "aave-v3", "apy": 4.5, "tvl": 8000000000, "chain": "Ethereum", "category": "Lending"},
            {"name": "Curve", "protocol_name": "curve", "apy": 6.0, "tvl": 5000000000, "chain": "Ethereum", "category": "DEX"},
            {"name": "Uniswap V3", "protocol_name": "uniswap-v3", "apy": 8.5, "tvl": 4000000000, "chain": "Ethereum", "category": "DEX"},
            {"name": "Compound", "protocol_name": "compound", "apy": 3.8, "tvl": 3000000000, "chain": "Ethereum", "category": "Lending"},
        ]
    
    async def _call_groq_for_generation(
        self,
        risk_preference: str,
        protocols: List[Dict]
    ) -> Dict[str, Any]:
        """Call Groq AI to generate vault strategy"""
        
        if not self.groq_client:
            logger.warning("[VAULT-AI] ⚠️ Groq not available, using fallback generation")
            return self._fallback_generation(risk_preference, protocols)
        
        try:
            # Build prompt
            system_prompt = """You are an expert DeFi portfolio strategist. Return ONLY valid JSON matching the schema below."""
            
            # Prepare protocol data with real yields (top 30 for better context)
            protocol_summary = []
            for p in protocols[:30]:
                protocol_summary.append({
                    "protocol": p.get("name", "Unknown"),
                    "protocol_name": p.get("protocol_name", "unknown"),
                    "apy": round(p.get("apy", 0), 2),
                    "tvl_usd": f"${p.get('tvl', 0):,.0f}",
                    "chain": p.get("chain", "Unknown"),
                    "category": p.get("category", "Unknown")
                })
            
            # Risk-specific guidance
            risk_guidance = {
                "low": "Focus on stable, established protocols with consistent yields (3-5% APY). Prioritize liquid staking and blue-chip lending.",
                "medium": "Balance between stability and yield (4-7% APY). Mix liquid staking, lending, and selective DEX pools.",
                "high": "Maximize yield potential (6-12% APY). Include leveraged strategies, newer protocols, and higher-risk DEX pools."
            }
            
            user_prompt = f"""You are analyzing LIVE DeFi yield data to create an optimal vault strategy.

📊 LIVE PROTOCOL DATA (Top 30 by TVL):
{json.dumps(protocol_summary, indent=2)}

🎯 USER REQUIREMENTS:
- Risk Tolerance: {risk_preference.upper()}
- Strategy Guidance: {risk_guidance.get(risk_preference, '')}

📋 YOUR TASK:
1. Analyze the live APY and TVL data above
2. Select 3-5 protocols that match the {risk_preference} risk profile
3. Allocate percentages that sum to exactly 100%
4. Calculate weighted expected APY: Σ(allocation% × protocol_apy)
5. Provide authentic reasoning based on ACTUAL protocol characteristics

⚠️ IMPORTANT:
- Use ONLY protocols from the data above
- Base reasoning on REAL APYs and categories shown
- For {risk_preference} risk: {risk_guidance.get(risk_preference, '')}
- Be specific: mention actual APYs, categories, and why each protocol fits

📤 RESPONSE FORMAT (JSON only):
{{
  "name": "AI [Risk] Yield Strategy v[N]",
  "description": "Brief strategy summary (1 sentence)",
  "risk_level": "{risk_preference}",
  "allocations": [
    {{"protocol_name": "lido", "percent": 40}},
    {{"protocol_name": "aave-v3", "percent": 30}},
    {{"protocol_name": "curve", "percent": 30}}
  ],
  "expected_apy": 4.5,
  "notes": "Detailed reasoning: Lido (3.2% APY) provides stable ETH staking base. Aave V3 (4.5% APY) adds lending yield. Curve (6.0% APY) boosts returns via LP fees. Weighted APY: (40%×3.2% + 30%×4.5% + 30%×6.0%) = 4.43%",
  "confidence": 0.87
}}

Return ONLY the JSON object, no markdown, no explanations outside JSON."""
            
            # Call Groq with lower temperature for data-driven responses
            logger.info(f"[VAULT-AI] 🧠 Sending strategy prompt to Groq ({settings.AI_MODEL})...")
            logger.info(f"[VAULT-AI] 📊 Using {len(protocol_summary)} protocols with live APY data")
            
            response = self.groq_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more deterministic, data-driven responses
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"[VAULT-AI] ✅ Groq response received ({len(response_text)} chars)")
            
            # Log sample of response for debugging
            logger.debug(f"[VAULT-AI] Response preview: {response_text[:200]}...")
            
            # Parse JSON
            vault_data = self._parse_json_safely(response_text)
            
            # Ensure required fields
            vault_data.setdefault("name", f"AI {risk_preference.title()} Vault")
            vault_data.setdefault("risk_level", risk_preference)
            vault_data.setdefault("confidence", 0.85)
            
            return vault_data
            
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Groq call failed: {e}")
            logger.warning("[VAULT-AI] ⚠️ Falling back to rule-based generation")
            return self._fallback_generation(risk_preference, protocols)
    
    async def _call_groq_for_refresh(
        self,
        vault: Dict,
        protocols: List[Dict]
    ) -> Dict[str, Any]:
        """Call Groq AI to re-evaluate vault"""
        
        if not self.groq_client:
            logger.warning("[VAULT-AI] ⚠️ Groq not available, using fallback refresh")
            return {"action": "no_change", "reason": "AI unavailable"}
        
        try:
            system_prompt = """You are an expert DeFi portfolio strategist. Return ONLY valid JSON matching the schema below."""
            
            # Prepare protocol data with live yields
            protocol_summary = []
            for p in protocols[:30]:
                protocol_summary.append({
                    "protocol": p.get("name", "Unknown"),
                    "protocol_name": p.get("protocol_name", "unknown"),
                    "apy": round(p.get("apy", 0), 2),
                    "tvl_usd": f"${p.get('tvl', 0):,.0f}",
                    "category": p.get("category", "Unknown")
                })
            
            current_allocs = vault.get('allocations', [])
            current_apy = vault.get('expected_apy', 0)
            
            user_prompt = f"""You are re-evaluating an existing vault with LIVE market data.

📊 CURRENT VAULT:
- Name: {vault.get('name')}
- Risk Level: {vault.get('risk_level')}
- Current APY: {current_apy:.2f}%
- Current Allocations: {json.dumps(current_allocs, indent=2)}

📈 LATEST LIVE PROTOCOL DATA (Top 30):
{json.dumps(protocol_summary, indent=2)}

🎯 YOUR TASK:
1. Compare current allocations against latest APYs
2. Calculate potential new weighted APY
3. Decide if update is worthwhile

⚠️ UPDATE CRITERIA:
- Update if: APY gain ≥ 0.5% OR allocation shift ≥ 10%
- Otherwise: Keep current strategy (no_change)

📤 RESPONSE FORMAT (JSON only):

Option A - No Change Needed:
{{
  "action": "no_change",
  "reason": "Current allocations remain optimal. Lido still at 3.2% APY, Aave at 4.5%. No significant market shifts detected."
}}

Option B - Update Recommended:
{{
  "action": "update",
  "new_allocations": [
    {{"protocol_name": "lido", "percent": 35}},
    {{"protocol_name": "aave-v3", "percent": 30}},
    {{"protocol_name": "curve", "percent": 35}}
  ],
  "expected_apy": 5.1,
  "reason": "Curve APY increased to 7.2% (+1.2%). Shifted 5% from Lido to Curve for +0.6% total APY gain.",
  "confidence": 0.88
}}

Return ONLY the JSON object."""
            
            # Call Groq with lower temperature for data-driven refresh
            logger.info(f"[VAULT-AI] 🔄 Re-evaluating vault with Groq ({settings.AI_MODEL})...")
            logger.info(f"[VAULT-AI] 📊 Current APY: {current_apy:.2f}% | Checking {len(protocol_summary)} protocols")
            
            response = self.groq_client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for objective comparison
                max_tokens=1200
            )
            
            response_text = response.choices[0].message.content.strip()
            update_data = self._parse_json_safely(response_text)
            
            return update_data
            
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Groq refresh call failed: {e}")
            return {"action": "no_change", "reason": f"AI error: {str(e)}"}
    
    def _fallback_generation(self, risk_preference: str, protocols: List[Dict]) -> Dict[str, Any]:
        """Fallback rule-based vault generation"""
        
        # Filter protocols by category and APY
        staking = [p for p in protocols if "staking" in p.get("category", "").lower()]
        lending = [p for p in protocols if "lending" in p.get("category", "").lower()]
        dex = [p for p in protocols if "dex" in p.get("category", "").lower()]
        
        # Sort by APY
        staking.sort(key=lambda x: x.get("apy", 0), reverse=True)
        lending.sort(key=lambda x: x.get("apy", 0), reverse=True)
        dex.sort(key=lambda x: x.get("apy", 0), reverse=True)
        
        # Build allocations based on risk
        allocations = []
        if risk_preference == "low":
            # Conservative: 60% staking, 30% lending, 10% DEX
            if staking: allocations.append({"protocol_name": staking[0]["name"].lower().replace(" ", "-"), "percent": 60})
            if lending: allocations.append({"protocol_name": lending[0]["name"].lower().replace(" ", "-"), "percent": 30})
            if dex: allocations.append({"protocol_name": dex[0]["name"].lower().replace(" ", "-"), "percent": 10})
        elif risk_preference == "high":
            # Aggressive: 30% staking, 30% lending, 40% DEX
            if staking: allocations.append({"protocol_name": staking[0]["name"].lower().replace(" ", "-"), "percent": 30})
            if lending: allocations.append({"protocol_name": lending[0]["name"].lower().replace(" ", "-"), "percent": 30})
            if dex: allocations.append({"protocol_name": dex[0]["name"].lower().replace(" ", "-"), "percent": 40})
        else:
            # Balanced: 50% staking, 30% lending, 20% DEX
            if staking: allocations.append({"protocol_name": staking[0]["name"].lower().replace(" ", "-"), "percent": 50})
            if lending: allocations.append({"protocol_name": lending[0]["name"].lower().replace(" ", "-"), "percent": 30})
            if dex: allocations.append({"protocol_name": dex[0]["name"].lower().replace(" ", "-"), "percent": 20})
        
        # Compute expected APY
        expected_apy = self.compute_expected_apy(allocations, protocols)
        
        return {
            "name": f"AI {risk_preference.title()} Vault (Fallback)",
            "description": f"Rule-based {risk_preference} risk vault with diversified allocations",
            "risk_level": risk_preference,
            "allocations": allocations,
            "expected_apy": expected_apy,
            "notes": "Generated using fallback rule-based logic",
            "confidence": 0.6
        }
    
    def compute_expected_apy(self, allocations: List[Dict], protocols: List[Dict]) -> float:
        """Compute weighted APY from allocations"""
        total_apy = 0.0
        total_percent = 0
        
        for alloc in allocations:
            protocol_name = alloc.get("protocol_name", "").lower()
            percent = alloc.get("percent", 0)
            
            # Find protocol
            protocol = next(
                (p for p in protocols if p.get("name", "").lower().replace(" ", "-") == protocol_name),
                None
            )
            
            if protocol:
                apy = protocol.get("apy", 0)
                total_apy += (percent / 100) * apy
                total_percent += percent
        
        # Normalize if total != 100
        if total_percent > 0 and total_percent != 100:
            total_apy = (total_apy / total_percent) * 100
        
        return round(total_apy, 2)
    
    def _validate_and_compute_apy(self, vault_data: Dict, protocols: List[Dict]) -> Dict:
        """Validate vault data and recompute APY"""
        
        # Ensure allocations sum to 100
        allocations = vault_data.get("allocations", [])
        total = sum(a.get("percent", 0) for a in allocations)
        
        if abs(total - 100) > 1:  # Allow 1% tolerance
            logger.warning(f"[VAULT-AI] ⚠️ Allocations sum to {total}%, normalizing to 100%")
            for alloc in allocations:
                alloc["percent"] = round((alloc["percent"] / total) * 100, 2)
        
        # Recompute expected APY
        vault_data["expected_apy"] = self.compute_expected_apy(allocations, protocols)
        
        return vault_data
    
    def _check_allocation_change(self, old: List[Dict], new: List[Dict]) -> bool:
        """Check if allocation change is significant (≥10% for any protocol)"""
        
        old_map = {a["protocol_name"]: a["percent"] for a in old}
        new_map = {a["protocol_name"]: a["percent"] for a in new}
        
        # Check for significant changes
        for protocol in set(list(old_map.keys()) + list(new_map.keys())):
            old_pct = old_map.get(protocol, 0)
            new_pct = new_map.get(protocol, 0)
            if abs(new_pct - old_pct) >= 10:
                return True
        
        return False
    
    def _parse_json_safely(self, text: str) -> Dict:
        """Parse JSON with recovery for malformed responses"""
        try:
            # Try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # Try to fix common issues (missing closing braces)
                text = text.strip()
                if not text.endswith("}"):
                    text += "}"
                if not text.endswith("]}"):
                    text += "]}"
                
                try:
                    return json.loads(text)
                except json.JSONDecodeError as e:
                    logger.error(f"[VAULT-AI] ❌ Failed to parse JSON: {e}")
                    logger.error(f"[VAULT-AI] Raw text: {text[:500]}")
                    raise ValueError("Failed to parse AI response as JSON")
    
    async def _save_vault_to_db(self, vault_data: Dict) -> int:
        """Save vault to database"""
        try:
            result = supabase.table("vaults").insert({
                "name": vault_data["name"],
                "description": vault_data.get("description", ""),
                "risk_level": vault_data["risk_level"],
                "expected_apy": vault_data["expected_apy"],
                "allocations": vault_data["allocations"],
                "ai_description": vault_data.get("notes", "")
            }).execute()
            
            vault_id = result.data[0]["id"]
            return vault_id
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to save vault: {e}")
            raise
    
    async def _get_vault_from_db(self, vault_id: int) -> Optional[Dict]:
        """Get vault from database"""
        try:
            result = supabase.table("vaults").select("*").eq("id", vault_id).execute()
            
            if not result.data:
                return None
            
            return result.data[0]
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to get vault: {e}")
            return None
    
    async def _update_vault_in_db(
        self,
        vault_id: int,
        allocations: List[Dict],
        expected_apy: float,
        ai_description: str
    ) -> Dict:
        """Update vault in database"""
        try:
            result = supabase.table("vaults").update({
                "allocations": allocations,
                "expected_apy": expected_apy,
                "ai_description": ai_description,
                "last_updated": datetime.now().isoformat()
            }).eq("id", vault_id).execute()
            
            return result.data[0]
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to update vault: {e}")
            raise
    
    async def _log_vault_event(
        self,
        vault_id: int,
        event_type: str,
        payload: Dict,
        summary: str,
        confidence: float,
        ai_model: str
    ):
        """Log vault AI event to database"""
        try:
            supabase.table("vault_ai_logs").insert({
                "vault_id": vault_id,
                "event_type": event_type,
                "payload": payload,
                "summary": summary,
                "confidence": confidence,
                "ai_model": ai_model
            }).execute()
        except Exception as e:
            logger.error(f"[VAULT-AI] ❌ Failed to log event: {e}")


# Singleton instance
vault_ai_service = VaultAIService()
