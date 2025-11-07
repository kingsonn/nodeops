"""
AI Agent Service

AI-powered portfolio analysis and recommendations using Groq LLaMA 3.1 70B.
Provides intelligent rebalancing suggestions based on APY, risk, and user preferences.
Fast, uncensored, and production-ready for DeFi analysis.
"""

import logging
import json
import re
import time
import aiohttp
import traceback
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
from cachetools import TTLCache
from groq import Groq

from backend.core.config import settings
from backend.services.portfolio import portfolio_service
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# In-memory cache for DeFi data (10 minute TTL)
defi_data_cache = TTLCache(maxsize=1, ttl=600)


class AIAgent:
    """AI Agent for portfolio analysis and rebalancing recommendations"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.groq_client = None
        self._initialize_groq()
    
    def _initialize_groq(self):
        """Initialize Groq API client"""
        if not settings.GROQ_API_KEY:
            logger.warning("Groq API key not configured")
            return
        
        try:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            logger.info(f"✓ Groq AI initialized (Model: {settings.AI_MODEL})")
            print(f"[AI-AGENT] ✓ Groq LLaMA 3.1 70B initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            print(f"[AI-AGENT] ❌ Groq initialization failed: {e}")
            self.groq_client = None
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self.supabase is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Supabase credentials not configured")
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("✓ Supabase client initialized for AI agent")
        return self.supabase
    
    def _safe_json_parse(self, ai_text: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse possibly truncated or malformed Gemini JSON responses.
        
        Attempts multiple recovery strategies:
        1. Standard JSON parsing
        2. Fix unclosed braces/brackets
        3. Extract first valid JSON object
        4. Attempt to complete truncated strings
        
        Args:
            ai_text: Raw text from Gemini API
            
        Returns:
            Parsed JSON dict or None if unrecoverable
        """
        if not ai_text or not ai_text.strip():
            print("[AI-AGENT] ERROR: Empty AI response text")
            return None
        
        # Remove Markdown code blocks or prefixes
        cleaned = ai_text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        print(f"[AI-AGENT] Attempting to parse JSON (length: {len(cleaned)} chars)")
        
        # Strategy 1: Try standard parsing first
        try:
            result = json.loads(cleaned)
            print(f"[AI-AGENT] ✅ Parsed JSON successfully (standard parsing)")
            return result
        except json.JSONDecodeError as e:
            print(f"[AI-AGENT] WARNING: Standard JSON parsing failed at position {e.pos}: {e.msg}")
        
        # Strategy 2: Try to fix unclosed braces or brackets
        print("[AI-AGENT] Attempting recovery: fixing unclosed braces...")
        try:
            # Count braces and brackets
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            open_brackets = cleaned.count('[')
            close_brackets = cleaned.count(']')
            
            # Add missing closing characters
            fixed = cleaned
            if open_braces > close_braces:
                fixed += '}' * (open_braces - close_braces)
                print(f"[AI-AGENT] Added {open_braces - close_braces} closing braces")
            if open_brackets > close_brackets:
                fixed += ']' * (open_brackets - close_brackets)
                print(f"[AI-AGENT] Added {open_brackets - close_brackets} closing brackets")
            
            result = json.loads(fixed)
            print(f"[AI-AGENT] ✅ Parsed JSON successfully (fixed unclosed braces)")
            return result
        except json.JSONDecodeError:
            print("[AI-AGENT] Recovery failed: could not fix with closing braces")
        
        # Strategy 3: Extract first valid JSON object
        print("[AI-AGENT] Attempting recovery: extracting first JSON object...")
        try:
            # Find the first complete JSON object
            match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
            if match:
                snippet = match.group(0)
                print(f"[AI-AGENT] Found JSON snippet (length: {len(snippet)} chars)")
                result = json.loads(snippet)
                print(f"[AI-AGENT] ✅ Parsed JSON successfully (extracted snippet)")
                return result
        except (json.JSONDecodeError, AttributeError):
            print("[AI-AGENT] Recovery failed: could not extract valid JSON object")
        
        # Strategy 4: Try to complete truncated strings
        print("[AI-AGENT] Attempting recovery: completing truncated strings...")
        try:
            # If text ends with an incomplete string, try to close it
            if cleaned.rstrip().endswith('"'):
                # Already has closing quote
                fixed = cleaned
            elif '"' in cleaned and not cleaned.rstrip().endswith('"'):
                # Add closing quote, then close objects
                fixed = cleaned.rstrip() + '"'
                open_braces = fixed.count('{')
                close_braces = fixed.count('}')
                if open_braces > close_braces:
                    fixed += '}' * (open_braces - close_braces)
            else:
                fixed = cleaned
            
            result = json.loads(fixed)
            print(f"[AI-AGENT] ✅ Parsed JSON successfully (completed truncated strings)")
            return result
        except json.JSONDecodeError:
            print("[AI-AGENT] Recovery failed: could not complete truncated strings")
        
        print("[AI-AGENT] ❌ Could not recover JSON. All strategies failed.")
        print(f"[AI-AGENT] Raw text sample: {cleaned[:200]}...")
        return None
    
    def _extract_gemini_text_safely(self, response) -> Optional[str]:
        """
        Safely extract text from Gemini response, handling various response formats.
        
        Args:
            response: Gemini API response object
            
        Returns:
            Extracted text or None if unavailable
        """
        text = ""
        
        try:
            # Method 1: Try direct .text accessor
            if hasattr(response, 'text') and response.text:
                text = response.text
                print(f"[AI-AGENT] ✅ Extracted text via .text accessor ({len(text)} chars)")
                return text
        except Exception as e:
            print(f"[AI-AGENT] .text accessor failed: {e}")
        
        try:
            # Method 2: Extract from candidates.content.parts
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text += part.text
                
                if text:
                    print(f"[AI-AGENT] ✅ Extracted text via candidates.content.parts ({len(text)} chars)")
                    return text
        except Exception as e:
            print(f"[AI-AGENT] candidates.content.parts extraction failed: {e}")
        
        print("[AI-AGENT] ⚠️ Failed to extract any text from Gemini response")
        return None
    
    def _create_minimal_fallback_response(self, wallet_address: str, message: str = "Fallback response") -> Dict[str, Any]:
        """Create a minimal valid response when Gemini fails completely"""
        return {
            "wallet": wallet_address,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_model": settings.AI_MODEL,
            "action": "hold",
            "recommendations": [],
            "expected_yield_increase": 0.0,
            "confidence": 0.0,
            "explanation": message,
            "fallback_mode": True,
            "ai_reasoning": {
                "category_analysis": "Unable to generate analysis",
                "optimization_directions": [],
                "risk_assessment": "Analysis unavailable"
            }
        }
    
    async def _get_live_defi_protocols(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch top DeFi protocols by TVL from DeFiLlama with live CoinGecko prices.
        Uses 10-minute TTL cache. Falls back to Supabase if APIs fail.
        """
        # Check cache first
        if "live_protocols" in defi_data_cache:
            cached_data = defi_data_cache["live_protocols"]
            print(f"[AI-AGENT] 💾 Using cached DeFi data ({len(cached_data)} protocols)")
            logger.info(f"💾 Using cached DeFi protocol data")
            return cached_data[:limit]
        
        try:
            defi_llama_url = "https://yields.llama.fi/pools"
            coingecko_url = "https://api.coingecko.com/api/v3/simple/price"
            
            print(f"[AI-AGENT] 🌐 Fetching live DeFi data from DeFiLlama...")
            logger.info("🌐 Fetching live DeFi data from DeFiLlama + CoinGecko")
            
            async with aiohttp.ClientSession() as session:
                # Fetch DeFiLlama pools
                async with session.get(defi_llama_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(f"DeFiLlama API error: {response.status}")
                        raise Exception(f"DeFiLlama returned status {response.status}")
                    
                    data = await response.json()
                    pools = data.get("data", [])
                    print(f"[AI-AGENT] Received {len(pools)} pools from DeFiLlama")
                
                # Filter and sort by TVL (only protocols with TVL > $10M)
                filtered_pools = [p for p in pools if p.get("tvlUsd", 0) > 10_000_000]
                sorted_pools = sorted(filtered_pools, key=lambda x: x.get("tvlUsd", 0), reverse=True)
                top_pools = sorted_pools[:200]  # Get top 200 for better selection
                
                print(f"[AI-AGENT] Filtered to {len(top_pools)} high-TVL protocols")
                
                # Extract unique project IDs for CoinGecko
                project_ids = {p.get("project", "").lower().replace(" ", "-") for p in top_pools if p.get("project")}
                project_ids = {pid for pid in project_ids if pid}  # Remove empty strings
                
                # Fetch CoinGecko prices
                prices = {}
                if project_ids:
                    ids_param = ",".join(list(project_ids)[:50])  # CoinGecko limit
                    coingecko_params = f"?ids={ids_param}&vs_currencies=usd"
                    
                    try:
                        async with session.get(
                            f"{coingecko_url}{coingecko_params}",
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as cg_response:
                            if cg_response.status == 200:
                                prices = await cg_response.json()
                                print(f"[AI-AGENT] Fetched prices for {len(prices)} protocols from CoinGecko")
                    except Exception as e:
                        logger.warning(f"CoinGecko API error (non-critical): {e}")
                        print(f"[AI-AGENT] ⚠️ CoinGecko prices unavailable: {e}")
            
            # Build enriched protocol list
            enriched = []
            for pool in top_pools:
                project = pool.get("project", "").lower().replace(" ", "-")
                enriched.append({
                    "protocol": pool.get("project", "Unknown"),
                    "chain": pool.get("chain", "Unknown"),
                    "category": pool.get("category", "Unknown"),
                    "tvl_usd": round(pool.get("tvlUsd", 0), 2),
                    "apy": round(pool.get("apy", 0), 2),
                    "price_usd": prices.get(project, {}).get("usd") if project in prices else None,
                    "symbol": pool.get("symbol", "")
                })
            
            # Cache the results
            defi_data_cache["live_protocols"] = enriched
            
            logger.info(f"📊 Cached {len(enriched)} live DeFi protocols (10 min TTL)")
            print(f"[AI-AGENT] 🌐 Cached {len(enriched)} live DeFi protocols from DeFiLlama & CoinGecko")
            
            return enriched[:limit]
            
        except Exception as e:
            logger.error(f"❌ DeFiLlama/CoinGecko fetch failed: {e}")
            print(f"[AI-AGENT] ⚠️ DeFiLlama/CoinGecko fetch failed: {e}")
            
            # Fallback to Supabase
            try:
                print("[AI-AGENT] ⚠️ Attempting Supabase fallback...")
                client = self._get_supabase_client()
                
                response = client.table("protocol_data").select(
                    "protocol_name,apy,tvl,chain,category"
                ).order("tvl", desc=True).limit(limit).execute()
                
                fallback_protocols = []
                for row in response.data:
                    fallback_protocols.append({
                        "protocol": row.get("protocol_name", "Unknown"),
                        "apy": float(row.get("apy", 0)) if row.get("apy") else 0.0,
                        "tvl_usd": float(row.get("tvl", 0)) if row.get("tvl") else 0.0,
                        "chain": row.get("chain", "Unknown"),
                        "category": row.get("category", "Unknown")
                    })
                
                logger.info(f"⚠️ Fallback: Loaded {len(fallback_protocols)} protocols from Supabase")
                print(f"[AI-AGENT] ⚠️ Fallback: Loaded {len(fallback_protocols)} protocols from Supabase")
                
                return fallback_protocols
                
            except Exception as fallback_error:
                logger.error(f"❌ Supabase fallback also failed: {fallback_error}")
                print(f"[AI-AGENT] ❌ Supabase fallback failed: {fallback_error}")
                return []
    
    def _calculate_portfolio_metrics(
        self,
        portfolio: Dict[str, Any],
        protocols: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate portfolio metrics and identify yield opportunities"""
        holdings = portfolio.get("holdings", [])
        total_value = float(portfolio.get("total_value_usd", 0))
        
        if not holdings or total_value == 0:
            return {
                "current_apy": 0.0,
                "market_avg_apy": 0.0,
                "opportunities": [],
                "potential_improvement": 0.0
            }
        
        # Calculate current weighted APY
        current_apy = sum(
            (h.get("value_usd", 0) / total_value) * h.get("apy", 0)
            for h in holdings
        )
        
        # Calculate market average APY (top 20 protocols)
        market_avg_apy = sum(p.get("apy", 0) for p in protocols[:20]) / min(len(protocols), 20) if protocols else 0.0
        
        # Identify better-yielding opportunities (≥1.5% higher APY)
        opportunities = []
        for protocol in protocols[:20]:
            protocol_apy = protocol.get("apy", 0)
            # Check if this protocol offers significantly better yield
            for holding in holdings:
                holding_apy = holding.get("apy", 0)
                apy_delta = protocol_apy - holding_apy
                
                if apy_delta >= 1.5:  # At least 1.5% better
                    opportunities.append({
                        "from_protocol": holding.get("protocol") or holding.get("protocol_name", "Unknown"),
                        "from_apy": holding_apy,
                        "to_protocol": protocol.get("protocol", "Unknown"),
                        "to_apy": protocol_apy,
                        "apy_delta": round(apy_delta, 2),
                        "tvl": protocol.get("tvl_usd", 0)
                    })
        
        # Sort opportunities by APY delta
        opportunities = sorted(opportunities, key=lambda x: x["apy_delta"], reverse=True)[:5]
        
        # Calculate potential improvement if user reallocates to top opportunity
        potential_improvement = opportunities[0]["apy_delta"] if opportunities else 0.0
        
        return {
            "current_apy": round(current_apy, 2),
            "market_avg_apy": round(market_avg_apy, 2),
            "opportunities": opportunities,
            "potential_improvement": round(potential_improvement, 2)
        }
    
    def _build_detailed_prompt(
        self,
        wallet_address: str,
        portfolio: Dict[str, Any],
        protocols: List[Dict[str, Any]],
        risk_preference: str
    ) -> str:
        """Build detailed prompt with full holdings and live market data for Gemini"""
        
        # Extract holdings details
        holdings = portfolio.get("holdings", [])
        total_value = Decimal(str(portfolio.get("total_value_usd", 0)))
        
        # Calculate portfolio metrics and opportunities
        metrics = self._calculate_portfolio_metrics(portfolio, protocols)
        
        # Format current holdings summary
        holdings_summary = []
        for h in holdings[:10]:
            protocol = h.get("protocol") or h.get("protocol_name", "Unknown")
            symbol = h.get("symbol") or h.get("token_symbol", "?")
            apy = h.get("apy", 0)
            value = h.get("value_usd", 0)
            holdings_summary.append(f"  - {protocol} ({symbol}) | {apy}% APY | ${value:.2f} value")
        
        holdings_text = "\n".join(holdings_summary) if holdings_summary else "  (No holdings)"
        
        # Format top 5 protocols by TVL
        top_protocols_summary = []
        for p in protocols[:5]:
            protocol = p.get("protocol", "Unknown")
            apy = p.get("apy", 0)
            tvl = p.get("tvl_usd", 0)
            top_protocols_summary.append(f"  - {protocol} | {apy}% APY | TVL ${tvl:,.0f}")
        
        top_protocols_text = "\n".join(top_protocols_summary) if top_protocols_summary else "  (No data)"
        
        # Format yield opportunities
        opportunities_text = ""
        if metrics["opportunities"]:
            opp_lines = []
            for opp in metrics["opportunities"][:3]:
                opp_lines.append(
                    f"  - Move from {opp['from_protocol']} ({opp['from_apy']}% APY) to "
                    f"{opp['to_protocol']} ({opp['to_apy']}% APY) → +{opp['apy_delta']}% yield improvement"
                )
            opportunities_text = "\n".join(opp_lines)
        else:
            opportunities_text = "  (No significant opportunities found)"
        
        prompt = f"""You are a professional DeFi strategist analyzing a user's portfolio.
Provide ACTIONABLE rebalancing recommendations to maximize yield while respecting risk preferences.

**User Wallet:** {wallet_address}
**Total Portfolio Value:** ${total_value:,.2f}
**Risk Preference:** {risk_preference}

**Current Portfolio Holdings ({len(holdings)} positions):**
{holdings_text}

**Portfolio Metrics:**
- Current Weighted APY: {metrics['current_apy']}%
- Market Average APY (Top 20): {metrics['market_avg_apy']}%
- Potential Improvement: +{metrics['potential_improvement']}%

**Top 5 DeFi Protocols by TVL (Live Data):**
{top_protocols_text}

**Identified Yield Opportunities:**
{opportunities_text}

**IMPORTANT INSTRUCTIONS:**
- Provide SPECIFIC rebalancing recommendations with percentages
- Calculate estimated yield improvement in percentage terms
- Suggest recommended allocations that total 100%
- Base reasoning on real protocol TVL and APY data provided above
- Do NOT make price predictions or investment advice
- Focus on yield optimization and risk-adjusted returns

**Your Task:**
1. Analyze current allocation and identify underperforming positions
2. Recommend SPECIFIC rebalancing actions (e.g., "Reallocate 25% from X to Y")
3. Calculate estimated yield improvement from suggested changes
4. Provide recommended final allocations (must total 100%)
5. Explain reasoning based on protocol stability, TVL, and APY data

**Return ONLY valid JSON in this EXACT format:**
{{
  "category_analysis": "Brief assessment of current allocation (2-3 sentences)",
  "optimization_directions": [
    "Reallocate 25% from [Protocol A] to [Protocol B] to increase yield by ~X%",
    "Add 10% allocation to [Protocol C] for diversification",
    "Reduce [Protocol D] exposure by 15% due to lower APY"
  ],
  "estimated_yield_improvement": "+1.2%",
  "recommended_allocations": {{
    "Protocol A": "30%",
    "Protocol B": "25%",
    "Protocol C": "20%",
    "Stables": "25%"
  }},
  "ai_reasoning": "Explanation of why these changes improve risk-adjusted returns based on TVL and APY data",
  "risk_assessment": "How recommendations align with {risk_preference} risk tolerance",
  "confidence": 0.85
}}

IMPORTANT: Return COMPLETE JSON. Include ALL fields. No markdown, no extra text."""

        return prompt
    
    def _parse_ai_recommendations(
        self,
        directions: List[str],
        holdings: List[Dict[str, Any]],
        protocols: List[Dict[str, Any]],
        risk_preference: str
    ) -> List[Dict[str, Any]]:
        """Parse specific recommendations from AI optimization directions"""
        import re
        recommendations = []
        
        print(f"[AI-AGENT] Attempting to parse {len(directions)} optimization directions...")
        
        # Build protocol APY map
        protocol_apy_map = {p.get("protocol", "").lower(): p.get("apy", 0) for p in protocols}
        
        for i, direction in enumerate(directions, 1):
            direction_lower = direction.lower()
            print(f"[AI-AGENT] Direction {i}: {direction}")
            
            # Pattern 1: "Reallocate X% from Y to Z" or "Move X% from Y to Z"
            match = re.search(r'(?:reallocate?|move)\s+(\d+)%?\s+from\s+([a-z0-9\s\-\.]+?)\s+to\s+([a-z0-9\s\-\.]+?)(?:\s|$|,|\.)', direction_lower)
            if match:
                percent = int(match.group(1))
                from_protocol = match.group(2).strip()
                to_protocol = match.group(3).strip()
                
                # Clean up protocol names (remove trailing words)
                from_protocol = from_protocol.split()[0] if from_protocol else from_protocol
                to_protocol = to_protocol.split()[0] if to_protocol else to_protocol
                
                # Get APY for target protocol
                target_apy = protocol_apy_map.get(to_protocol, 0)
                if target_apy == 0:
                    # Try partial match
                    for proto_name, apy in protocol_apy_map.items():
                        if to_protocol in proto_name or proto_name in to_protocol:
                            target_apy = apy
                            break
                
                recommendations.append({
                    "from": from_protocol.title(),
                    "to": to_protocol.title(),
                    "percent": percent,
                    "apy": target_apy,
                    "reason": f"AI suggested reallocation to improve yield"
                })
                print(f"[AI-AGENT] ✅ Parsed: Move {percent}% from {from_protocol} to {to_protocol} (APY: {target_apy}%)")
                continue
            else:
                print(f"[AI-AGENT] ⚠️ Pattern 1 didn't match")
            
            # Pattern 2: "Add X% allocation to Y"
            match = re.search(r'add\s+(\d+)%?\s+(?:allocation\s+)?to\s+([a-z0-9\s\-\.]+?)(?:\s|$|,|\.)', direction_lower)
            if match:
                percent = int(match.group(1))
                to_protocol = match.group(2).strip().split()[0]
                
                # Find largest holding to reduce from
                if holdings:
                    largest_holding = max(holdings, key=lambda h: h.get("value_usd", 0))
                    from_protocol = largest_holding.get("protocol") or largest_holding.get("protocol_name", "Unknown")
                    
                    target_apy = protocol_apy_map.get(to_protocol, 0)
                    if target_apy == 0:
                        for proto_name, apy in protocol_apy_map.items():
                            if to_protocol in proto_name or proto_name in to_protocol:
                                target_apy = apy
                                break
                    
                    recommendations.append({
                        "from": from_protocol,
                        "to": to_protocol.title(),
                        "percent": percent,
                        "apy": target_apy,
                        "reason": f"AI suggested adding exposure to {to_protocol}"
                    })
                    print(f"[AI-AGENT] ✅ Parsed: Add {percent}% to {to_protocol} from {from_protocol} (APY: {target_apy}%)")
                continue
            else:
                print(f"[AI-AGENT] ⚠️ Pattern 2 didn't match")
            
            # Pattern 3: "Reduce X by Y%"
            match = re.search(r'reduce\s+([a-z0-9\s\-\.]+?)\s+(?:by\s+|exposure\s+by\s+)?(\d+)%', direction_lower)
            if match:
                from_protocol = match.group(1).strip().split()[0]
                percent = int(match.group(2))
                
                # Find best protocol to move to
                if protocols:
                    best_protocol = max(protocols[:10], key=lambda p: p.get("apy", 0))
                    to_protocol = best_protocol.get("protocol", "Unknown")
                    target_apy = best_protocol.get("apy", 0)
                    
                    recommendations.append({
                        "from": from_protocol.title(),
                        "to": to_protocol,
                        "percent": percent,
                        "apy": target_apy,
                        "reason": f"AI suggested reducing {from_protocol} exposure"
                    })
                    print(f"[AI-AGENT] ✅ Parsed: Reduce {from_protocol} by {percent}%, move to {to_protocol} (APY: {target_apy}%)")
                continue
            else:
                print(f"[AI-AGENT] ⚠️ Pattern 3 didn't match")
                print(f"[AI-AGENT] ❌ No patterns matched for this direction")
        
        print(f"[AI-AGENT] Total recommendations parsed: {len(recommendations)}")
        return recommendations
    
    def _detect_optimization_keywords(self, directions: List[str]) -> List[Dict[str, str]]:
        """Detect optimization keywords and map to category actions"""
        actions = []
        
        for direction in directions:
            direction_lower = direction.lower()
            
            # Detect increase/add keywords
            if any(word in direction_lower for word in ["increase", "add", "more", "boost", "expand"]):
                # Extract category
                if "staking" in direction_lower or "stake" in direction_lower:
                    actions.append({"action": "increase", "category": "Staking"})
                elif "lending" in direction_lower or "lend" in direction_lower:
                    actions.append({"action": "increase", "category": "Lending"})
                elif "liquidity" in direction_lower or "dex" in direction_lower or "amm" in direction_lower:
                    actions.append({"action": "increase", "category": "Liquidity"})
                elif "yield" in direction_lower or "farming" in direction_lower:
                    actions.append({"action": "increase", "category": "Yield Farming"})
            
            # Detect decrease/reduce keywords
            elif any(word in direction_lower for word in ["reduce", "decrease", "less", "lower", "minimize"]):
                if "staking" in direction_lower or "stake" in direction_lower:
                    actions.append({"action": "decrease", "category": "Staking"})
                elif "lending" in direction_lower or "lend" in direction_lower:
                    actions.append({"action": "decrease", "category": "Lending"})
                elif "liquidity" in direction_lower or "dex" in direction_lower:
                    actions.append({"action": "decrease", "category": "Liquidity"})
                elif "yield" in direction_lower or "farming" in direction_lower:
                    actions.append({"action": "decrease", "category": "Yield Farming"})
        
        return actions
    
    def _generate_numeric_recommendations(
        self,
        portfolio: Dict[str, Any],
        protocols: List[Dict[str, Any]],
        actions: List[Dict[str, str]],
        risk_preference: str
    ) -> List[Dict[str, Any]]:
        """Generate numeric rebalancing recommendations based on qualitative actions"""
        recommendations = []
        
        if not actions:
            return recommendations
        
        # Group holdings by category
        holdings_by_category = {}
        for holding in portfolio["holdings"]:
            category = holding.get("category", "unknown")
            if category not in holdings_by_category:
                holdings_by_category[category] = []
            holdings_by_category[category].append(holding)
        
        # Group protocols by category
        protocols_by_category = {}
        for protocol in protocols:
            category = protocol.get("category", "unknown")
            if category not in protocols_by_category:
                protocols_by_category[category] = []
            protocols_by_category[category].append(protocol)
        
        # Process each action
        for action in actions:
            action_type = action["action"]
            target_category = action["category"]
            
            if action_type == "increase":
                # Find source category to reduce (pick highest allocation)
                source_category = None
                max_value = 0
                for cat, holdings in holdings_by_category.items():
                    if cat != target_category:
                        cat_value = sum(h["value_usd"] for h in holdings)
                        if cat_value > max_value:
                            max_value = cat_value
                            source_category = cat
                
                if source_category and source_category in holdings_by_category:
                    # Pick best protocol in target category
                    target_protocols = protocols_by_category.get(target_category, [])
                    if target_protocols:
                        # Sort by APY, filter by risk
                        target_protocols = sorted(target_protocols, key=lambda p: p["apy"], reverse=True)
                        best_target = target_protocols[0]
                        
                        # Pick protocol to reduce from source category (lowest APY)
                        source_holdings = holdings_by_category[source_category]
                        source_holdings = sorted(source_holdings, key=lambda h: h["apy"])
                        worst_source = source_holdings[0]
                        
                        # Determine rebalance percentage based on risk preference
                        if risk_preference == "low":
                            percent = 15
                        elif risk_preference == "high":
                            percent = 30
                        else:  # medium
                            percent = 20
                        
                        recommendations.append({
                            "from": worst_source["protocol"],
                            "to": best_target["name"],
                            "percent": percent,
                            "reason": f"Increase {target_category} exposure by reducing {source_category} concentration"
                        })
            
            elif action_type == "decrease":
                # Reduce this category, spread to others
                if target_category in holdings_by_category:
                    source_holdings = holdings_by_category[target_category]
                    if source_holdings:
                        # Pick lowest APY in this category
                        source_holdings = sorted(source_holdings, key=lambda h: h["apy"])
                        worst_source = source_holdings[0]
                        
                        # Find best protocol in other categories
                        best_target = None
                        best_apy = 0
                        for cat, protos in protocols_by_category.items():
                            if cat != target_category and protos:
                                for proto in protos:
                                    if proto["apy"] > best_apy:
                                        best_apy = proto["apy"]
                                        best_target = proto
                        
                        if best_target:
                            if risk_preference == "low":
                                percent = 15
                            elif risk_preference == "high":
                                percent = 30
                            else:
                                percent = 20
                            
                            recommendations.append({
                                "from": worst_source["protocol"],
                                "to": best_target["name"],
                                "percent": percent,
                                "reason": f"Reduce {target_category} concentration for better diversification"
                            })
        
        return recommendations
    
    def _calculate_expected_yield_increase(
        self,
        portfolio: Dict[str, Any],
        recommendations: List[Dict[str, Any]]
    ) -> float:
        """Calculate expected yield increase from recommendations"""
        if not recommendations:
            return 0.0
        
        total_value = portfolio["total_value_usd"]
        if total_value == 0:
            return 0.0
        
        # Calculate current weighted APY
        current_apy = sum(
            (h["value_usd"] / total_value) * h["apy"]
            for h in portfolio["holdings"]
        )
        
        # Estimate new APY (simplified)
        # This is a rough estimate - the simulation engine will do precise calculation
        estimated_improvement = len(recommendations) * 0.3  # ~0.3% per recommendation
        
        return round(estimated_improvement, 2)
    
    async def analyze_portfolio(self, wallet_address: str) -> Dict[str, Any]:
        """
        Analyze portfolio and generate AI-powered rebalancing recommendations
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            AI analysis with recommendations
        """
        try:
            logger.info(f"🤖 AI analysis started for wallet: {wallet_address}")
            print(f"[AI-AGENT] Starting analysis for wallet: {wallet_address}")
            
            # 1. Fetch user portfolio with full holdings details
            portfolio = await portfolio_service.get_user_portfolio(wallet_address)
            if not portfolio:
                print(f"[AI-AGENT] Portfolio not found for wallet: {wallet_address}")
                raise ValueError(f"Portfolio not found for wallet: {wallet_address}")
            
            holdings = portfolio.get("holdings", [])
            total_value = Decimal(str(portfolio.get("total_value_usd", 0)))
            
            print(f"[AI-AGENT] Portfolio loaded: {len(holdings)} holdings, ${total_value:,.2f} total")
            
            if not holdings:
                print("[AI-AGENT] ⚠️ No holdings found — using empty fallback")
            
            # Log top holdings for transparency (with proper protocol_name handling)
            print("[AI-AGENT] User Holdings (top 5):")
            for h in holdings[:5]:
                # Try multiple field names for protocol
                protocol = h.get("protocol_name") or h.get("protocol") or "Unknown"
                symbol = h.get("token_symbol") or h.get("symbol") or "?"
                amount = h.get("amount", 0)
                value = h.get("value_usd", 0)
                apy = h.get("apy", 0)
                print(f"  - {protocol} ({symbol}) | Amount: {amount} | Value: ${value:.2f} | APY: {apy}%")
            
            # 2. Fetch live DeFi protocol data from DeFiLlama + CoinGecko
            protocols = await self._get_live_defi_protocols(limit=50)
            if not protocols:
                logger.warning("No live protocol data available, using portfolio data only")
                print("[AI-AGENT] WARNING: No live protocol data available")
            else:
                print(f"[AI-AGENT] Loaded {len(protocols)} live protocols for analysis")
                
                # Log top protocols for transparency
                print("[AI-AGENT] Top 5 Live Protocols by TVL:")
                for p in protocols[:5]:
                    protocol_name = p.get("protocol", "Unknown")
                    tvl = p.get("tvl_usd", 0)
                    apy = p.get("apy", 0)
                    chain = p.get("chain", "Unknown")
                    print(f"  - {protocol_name} | TVL: ${tvl:,.0f} | APY: {apy}% | Chain: {chain}")
            
            # 3. Check if Groq client is available
            if not self.groq_client:
                logger.warning("Groq client not initialized, returning rule-based analysis")
                print("[AI-AGENT] Groq client not initialized, using fallback")
                return await self._fallback_analysis(portfolio, protocols)
            
            # 4. Build detailed prompt with full holdings and live market data
            risk_preference = portfolio.get("risk_preference", "medium")
            prompt = self._build_detailed_prompt(wallet_address, portfolio, protocols, risk_preference)
            
            # Build simple fallback prompt (for retry if blocked)
            holdings_count = len(portfolio.get("holdings", []))
            total_value = portfolio.get("total_value_usd", 0)
            safe_fallback_prompt = f"""Analyze this DeFi portfolio allocation data neutrally.

Portfolio: {holdings_count} holdings, ${total_value:.2f} total value
Risk preference: {risk_preference}

Provide a brief JSON summary:
{{
  "category_analysis": "Current allocation summary",
  "optimization_directions": ["general observation 1", "general observation 2"],
  "risk_assessment": "Allocation pattern description",
  "confidence": 0.75
}}"""
            
            # Check and manage prompt size
            prompt_size = len(prompt)
            
            # If prompt is too large, truncate protocol data
            if prompt_size > 8000:
                print(f"[AI-AGENT] ⚠️ Prompt too large ({prompt_size} chars), truncating protocol data...")
                # Rebuild with fewer protocols
                prompt = self._build_detailed_prompt(wallet_address, portfolio, protocols[:25], risk_preference)
                prompt_size = len(prompt)
                print(f"[AI-AGENT] Truncated prompt size: {prompt_size} chars")
            
            logger.info(f"📝 Sending detailed prompt to Groq LLaMA (size: {prompt_size:,} chars)...")
            print(f"[AI-AGENT] Final prompt size: {prompt_size} chars")
            print(f"[AI-AGENT] Sending prompt to Groq LLaMA 3.1 70B for wallet: {wallet_address}")
            print(f"[AI-AGENT] Prompt preview (first 400 chars):\n{prompt[:400]}...")
            
            # 5. Call Groq LLaMA 3.1 70B for portfolio reasoning
            start_time = time.time()
            
            # Check if Groq client is initialized
            if not self.groq_client:
                logger.warning("Groq client not initialized, using fallback")
                print("[AI-AGENT] Groq client not initialized, using fallback")
                return await self._fallback_analysis(portfolio, protocols)
            
            response_text = None
            
            try:
                print("[AI-AGENT] Calling Groq LLaMA 3.1 70B...")
                call_start = time.time()
                
                response = self.groq_client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert DeFi portfolio analyst. Provide data-driven, qualitative analysis without financial advice."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=settings.AI_TEMPERATURE,
                    max_tokens=1000,
                    top_p=0.95,
                )
                
                call_elapsed_ms = round((time.time() - call_start) * 1000)
                print(f"[AI-AGENT] Groq response time: {call_elapsed_ms}ms")
                
                # Extract response text
                if response.choices and len(response.choices) > 0:
                    response_text = response.choices[0].message.content.strip()
                    print(f"[AI-AGENT] ✅ Groq returned valid text ({len(response_text)} chars)")
                    print(f"[AI-AGENT] Response preview (first 300 chars): {response_text[:300]}...")
                else:
                    print("[AI-AGENT] ⚠️ No response choices available")
                    raise ValueError("Groq returned no valid response")
                    
            except Exception as e:
                logger.error(f"❌ Groq API error: {e}")
                print(f"[AI-AGENT] WARNING: Groq call failed: {e}")
                traceback.print_exc()
                
                # Retry with simpler fallback prompt
                print("[AI-AGENT] Retrying with simpler fallback prompt...")
                try:
                    retry_start = time.time()
                    
                    safe_response = self.groq_client.chat.completions.create(
                        model=settings.AI_MODEL,
                        messages=[
                            {"role": "system", "content": "You are a DeFi analyst. Return only valid JSON."},
                            {"role": "user", "content": safe_fallback_prompt}
                        ],
                        temperature=0.2,  # Lower temperature for retry
                        max_tokens=512,
                    )
                    
                    retry_elapsed_ms = round((time.time() - retry_start) * 1000)
                    print(f"[AI-AGENT] Retry response time: {retry_elapsed_ms}ms")
                    
                    if safe_response.choices and len(safe_response.choices) > 0:
                        response_text = safe_response.choices[0].message.content.strip()
                        print(f"[AI-AGENT] ✅ Fallback prompt returned valid text")
                        print(f"[AI-AGENT] Fallback response preview: {response_text[:300]}...")
                    else:
                        print("[AI-AGENT] ❌ Fallback prompt also returned no valid text")
                        response_text = None
                        
                except Exception as retry_error:
                    print(f"[AI-AGENT] ❌ Fallback prompt failed: {retry_error}")
                    response_text = None
                
                # If both attempts failed, use rule-based fallback
                if not response_text:
                    print("[AI-AGENT] ❌ No valid text returned after retry. Using rule-based fallback.")
                    return await self._fallback_analysis(portfolio, protocols)
            
            elapsed = time.time() - start_time
            logger.info(f"🤖 Groq LLaMA reasoning complete in {elapsed:.2f}s")
            print(f"[AI-AGENT] Total Groq interaction time: {elapsed:.2f}s")
            
            # Check if response is valid
            if not response_text:
                print("[AI-AGENT] WARNING: No valid response text")
                return await self._fallback_analysis(portfolio, protocols)
            
            # Use safe JSON parser with recovery logic
            print(f"[AI-AGENT] Raw Groq response (length: {len(response_text)} chars)")
            print(f"[AI-AGENT] Response preview: {response_text[:300]}...")
            
            qualitative_result = self._safe_json_parse(response_text)
            
            if qualitative_result:
                print(f"[AI-AGENT] ✅ Parsed Groq response successfully (parsed length: {len(json.dumps(qualitative_result))} chars)")
                logger.info(f"✓ Groq qualitative JSON parsed successfully")
            else:
                print("[AI-AGENT] ⚠️ Using rule-based fallback (Groq output not recoverable)")
                logger.error(f"❌ Failed to parse Groq response after all recovery attempts")
                logger.error(f"Response text (first 500 chars): {response_text[:500]}")
                return await self._fallback_analysis(portfolio, protocols)
            
            # 7. Extract AI recommendations
            optimization_directions = qualitative_result.get("optimization_directions", [])
            category_analysis = qualitative_result.get("category_analysis", "")
            risk_assessment = qualitative_result.get("risk_assessment", "")
            ai_confidence = qualitative_result.get("confidence", 0.8)
            estimated_yield_improvement = qualitative_result.get("estimated_yield_improvement", "0%")
            recommended_allocations = qualitative_result.get("recommended_allocations", {})
            ai_reasoning = qualitative_result.get("ai_reasoning", "")
            
            # If recommended_allocations is empty or doesn't match directions, derive from current holdings
            if not recommended_allocations or len(recommended_allocations) == 0:
                print("[AI-AGENT] No recommended_allocations from AI, deriving from current holdings...")
                # Build allocations from current holdings as baseline
                recommended_allocations = {}
                for h in holdings[:5]:  # Top 5 holdings
                    protocol = h.get("protocol") or h.get("protocol_name", "Unknown")
                    percentage = (h.get("value_usd", 0) / total_value * 100) if total_value > 0 else 0
                    if percentage > 1:  # Only include if > 1%
                        recommended_allocations[protocol] = f"{percentage:.0f}%"
            
            print(f"[AI-AGENT] Extracted {len(optimization_directions)} optimization directions")
            print(f"[AI-AGENT] Estimated yield improvement: {estimated_yield_improvement}")
            print(f"[AI-AGENT] AI confidence: {ai_confidence}")
            
            # Log actionable insights summary
            if optimization_directions:
                print("[AI-AGENT] 📊 Actionable Insights:")
                for i, direction in enumerate(optimization_directions[:3], 1):
                    print(f"  {i}. {direction}")
            
            logger.info(f"📊 AI suggested {len(optimization_directions)} rebalancing actions with {estimated_yield_improvement} yield improvement")
            
            # 8. Parse AI optimization directions into recommendations
            # Try to extract specific recommendations from AI directions
            recommendations = self._parse_ai_recommendations(
                optimization_directions, holdings, protocols, risk_preference
            )
            
            # If no specific recommendations found, try keyword detection
            if not recommendations:
                print("[AI-AGENT] No specific recommendations found, trying keyword detection...")
                actions = self._detect_optimization_keywords(optimization_directions)
                logger.info(f"🔍 Detected {len(actions)} actionable insights from AI reasoning")
                
                # 9. Generate numeric recommendations using local simulation engine
                logger.info("⚙️ Local engine generating rebalancing simulation...")
                recommendations = self._generate_numeric_recommendations(
                    portfolio, protocols, actions, risk_preference
                )
            else:
                print(f"[AI-AGENT] Parsed {len(recommendations)} specific recommendations from AI")
                logger.info(f"✅ Parsed {len(recommendations)} specific recommendations from AI directions")
            
            # 10. Calculate expected yield increase
            expected_yield_increase = self._calculate_expected_yield_increase(
                portfolio, recommendations
            )
            
            # 11. Determine action - Always rebalance if AI provided any optimization directions
            action = "rebalance" if (recommendations or optimization_directions) else "hold"
            
            # 12. Build combined explanation with yield improvement
            # If AI provided optimization directions, use them even if recommendations parsing failed
            if recommendations or (optimization_directions and len(optimization_directions) > 0):
                if ai_reasoning:
                    explanation = f"{category_analysis} {ai_reasoning} Estimated yield improvement: {estimated_yield_improvement}."
                else:
                    explanation = f"{category_analysis} Based on current market opportunities, consider the suggested rebalancing to optimize yield."
            else:
                explanation = f"{category_analysis} Your current allocation appears well-balanced for your {risk_preference} risk preference."
            
            # 13. Sanitize recommendations to prevent KeyErrors
            sanitized_recommendations = []
            for rec in recommendations:
                sanitized_rec = {
                    "from": rec.get("from") or rec.get("protocol") or "Unknown",
                    "to": rec.get("to") or rec.get("target") or "Unknown",
                    "percent": rec.get("percent", 0),
                    "reason": rec.get("reason", "Optimization opportunity identified")
                }
                sanitized_recommendations.append(sanitized_rec)
            
            print(f"[AI-AGENT] Sanitized {len(sanitized_recommendations)} recommendations")
            
            # 14. Build final result combining AI reasoning + local computation
            result = {
                "wallet": wallet_address,
                "timestamp": datetime.utcnow().isoformat(),
                "ai_model": settings.AI_MODEL,
                "action": action,
                "recommendations": sanitized_recommendations,
                "expected_yield_increase": expected_yield_increase,
                "estimated_yield_improvement": estimated_yield_improvement,
                "recommended_allocations": recommended_allocations,
                "confidence": ai_confidence,
                "explanation": explanation,
                "ai_reasoning": {
                    "category_analysis": category_analysis,
                    "optimization_directions": optimization_directions,
                    "risk_assessment": risk_assessment,
                    "ai_reasoning": ai_reasoning
                }
            }
            
            total_time = time.time() - start_time
            logger.info(f"⚙️ Local engine generated {len(sanitized_recommendations)} numeric recommendations")
            logger.info(f"✅ Combined analysis ready in {total_time:.2f}s: {action} with {len(sanitized_recommendations)} recommendations")
            print(f"[AI-AGENT] ✅ Final parsed response with {len(sanitized_recommendations)} recommendations")
            
            # 15. Record decision
            await self.record_ai_decision(wallet_address, result)
            
            # 16. Run simulation automatically with AI result
            print(f"[AI-AGENT] ⚙️ Running automatic simulation...")
            simulation = await self._simulate_with_ai_result(wallet_address, result, portfolio, protocols)
            
            # 17. Return combined AI + simulation response
            combined_result = {
                "ai_result": result,
                "simulation": simulation
            }
            
            print(f"[AI-AGENT] ✅ Combined AI + Simulation Response Ready")
            logger.info(f"✅ Combined AI + Simulation complete in {time.time() - start_time:.2f}s")
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            raise
    
    async def _fallback_analysis(
        self,
        portfolio: Dict[str, Any],
        protocols: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback rule-based analysis when Gemini is unavailable"""
        
        logger.info("Using rule-based fallback analysis")
        
        # Simple rule: suggest moving to highest APY protocol
        current_holdings = portfolio["holdings"]
        
        if not current_holdings or not protocols:
            return {
                "wallet": portfolio["wallet_address"],
                "action": "hold",
                "recommendations": [],
                "expected_yield_increase": 0.0,
                "confidence": 0.5,
                "explanation": "Insufficient data for analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "ai_model": "rule-based-fallback"
            }
        
        # Find highest APY protocol
        sorted_protocols = sorted(protocols, key=lambda p: p["apy"], reverse=True)
        best_protocol = sorted_protocols[0] if sorted_protocols else None
        
        # Find lowest APY holding
        sorted_holdings = sorted(current_holdings, key=lambda h: h["apy"])
        worst_holding = sorted_holdings[0] if sorted_holdings else None
        
        recommendations = []
        if best_protocol and worst_holding and best_protocol["apy"] > worst_holding["apy"]:
            recommendations.append({
                "from": worst_holding["protocol"],
                "to": best_protocol["name"],
                "percent": 20,
                "reason": f"Higher APY ({best_protocol['apy']:.2f}% vs {worst_holding['apy']:.2f}%)"
            })
        
        return {
            "wallet": portfolio["wallet_address"],
            "action": "rebalance" if recommendations else "hold",
            "recommendations": recommendations,
            "expected_yield_increase": 0.5 if recommendations else 0.0,
            "confidence": 0.6,
            "explanation": "Rule-based analysis: Move funds to higher APY protocol" if recommendations else "Current allocation acceptable",
            "timestamp": datetime.utcnow().isoformat(),
            "ai_model": "rule-based-fallback"
        }
    
    async def _simulate_with_ai_result(
        self,
        wallet_address: str,
        ai_result: Dict[str, Any],
        portfolio: Dict[str, Any],
        protocols: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulate rebalancing using provided AI result (no redundant API call)
        
        Args:
            wallet_address: User's wallet address
            ai_result: AI analysis result with recommendations
            portfolio: Current portfolio data
            protocols: Live protocol data for APY lookup
            
        Returns:
            Simulation results with before/after state
        """
        try:
            print(f"[AI-AGENT] ⚙️ Running in-line simulation for {wallet_address}...")
            
            holdings = portfolio.get("holdings", [])
            total_value = portfolio.get("total_value_usd", 0)
            
            # Fetch protocols if not provided
            if not protocols:
                protocols = await self._get_live_defi_protocols(limit=50)
            
            # Build protocol APY map for quick lookup
            protocol_apy_map = {}
            for p in protocols:
                protocol_name = p.get("protocol", "").lower()
                protocol_apy_map[protocol_name] = p.get("apy", 0)
            
            # Handle empty portfolio
            if not holdings or total_value <= 0:
                return {
                    "status": "empty",
                    "message": "Portfolio empty. Simulation skipped.",
                    "before_total_apy": 0.0,
                    "after_total_apy": 0.0,
                    "apy_increase": 0.0,
                    "expected_gain_usd": 0.0
                }
            
            recommendations = ai_result.get("recommendations", [])
            
            # Handle no recommendations
            if not recommendations:
                current_apy = self._calculate_weighted_apy(holdings, total_value)
                return {
                    "status": "no_recommendations",
                    "message": "No actionable AI recommendations found.",
                    "before_total_apy": round(current_apy, 2),
                    "after_total_apy": round(current_apy, 2),
                    "apy_increase": 0.0,
                    "expected_gain_usd": 0.0,
                    "confidence": ai_result.get("confidence", 0.0),
                    "explanation": ai_result.get("explanation", "")
                }
            
            # Calculate current weighted APY
            before_apy = self._calculate_weighted_apy(holdings, total_value)
            print(f"[AI-AGENT] Current portfolio APY: {before_apy:.2f}%")
            
            # Apply recommendations to simulate new holdings
            new_holdings = [h.copy() for h in holdings]
            print(f"[AI-AGENT] Applying {len(recommendations)} recommendations to portfolio...")
            
            for rec in recommendations:
                from_protocol = rec.get("from", "").lower()
                to_protocol = rec.get("to", "").lower()
                percent = rec.get("percent", 0)
                
                if not from_protocol or not to_protocol or percent <= 0:
                    continue
                
                # Find source holding (try multiple field names)
                from_holding = next(
                    (h for h in new_holdings 
                     if (h.get("protocol_name", "").lower() == from_protocol or 
                         h.get("protocol", "").lower() == from_protocol)),
                    None
                )
                
                if not from_holding:
                    print(f"[AI-AGENT] ⚠️ Missing source protocol: {from_protocol}")
                    print(f"[AI-AGENT] Available protocols: {[h.get('protocol', h.get('protocol_name', '?')).lower() for h in new_holdings]}")
                    continue
                
                # Calculate amount to move
                move_value = (percent / 100) * from_holding.get("value_usd", 0)
                print(f"[AI-AGENT] Moving {percent}% (${move_value:.2f}) from {from_protocol} (APY: {from_holding.get('apy', 0)}%) to {to_protocol}")
                
                # Reduce source
                from_holding["value_usd"] = from_holding.get("value_usd", 0) - move_value
                
                # Find or create target holding
                to_holding = next(
                    (h for h in new_holdings 
                     if (h.get("protocol_name", "").lower() == to_protocol or 
                         h.get("protocol", "").lower() == to_protocol)),
                    None
                )
                
                if to_holding:
                    to_holding["value_usd"] = to_holding.get("value_usd", 0) + move_value
                else:
                    # Create new holding with APY from live protocol data
                    target_apy = protocol_apy_map.get(to_protocol, rec.get("apy", 5.0))
                    print(f"[AI-AGENT] Creating new holding: {to_protocol.title()} with APY {target_apy}%")
                    new_holdings.append({
                        "protocol_name": to_protocol.title(),
                        "protocol": to_protocol.title(),
                        "value_usd": move_value,
                        "apy": target_apy,  # Use live APY from protocol data
                        "amount": 0,
                        "token_symbol": to_protocol[:4].upper()
                    })
            
            # Remove holdings with negligible value
            new_holdings = [h for h in new_holdings if h.get("value_usd", 0) > 0.01]
            
            # Calculate new weighted APY
            after_apy = self._calculate_weighted_apy(new_holdings, total_value)
            
            # Calculate expected gains
            apy_increase = after_apy - before_apy
            expected_gain_usd = (total_value * apy_increase) / 100
            
            result = {
                "status": "success",
                "before_total_apy": round(before_apy, 2),
                "after_total_apy": round(after_apy, 2),
                "apy_increase": round(apy_increase, 2),
                "expected_gain_usd": round(expected_gain_usd, 2),
                "confidence": ai_result.get("confidence", 0.0),
                "explanation": ai_result.get("explanation", ""),
                "recommendations": recommendations
            }
            
            print(f"[AI-AGENT] ✅ Simulation complete: APY {before_apy:.2f}% → {after_apy:.2f}% (+${expected_gain_usd:.2f}/year)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            print(f"[AI-AGENT] ❌ Simulation failed: {e}")
            return {
                "status": "error",
                "message": f"Simulation error: {str(e)}",
                "before_total_apy": 0.0,
                "after_total_apy": 0.0,
                "apy_increase": 0.0,
                "expected_gain_usd": 0.0
            }
    
    async def simulate_rebalance(self, wallet_address: str) -> Dict[str, Any]:
        """
        Simulate rebalancing based on AI recommendations
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            Simulation results with before/after state
        """
        try:
            logger.info(f"🎯 Starting rebalance simulation for {wallet_address}")
            
            # 1. Get combined AI analysis + simulation (now returns both)
            combined = await self.analyze_portfolio(wallet_address)
            
            # 2. Return the simulation part (for backward compatibility)
            # Note: analyze_portfolio now returns {"ai_result": {...}, "simulation": {...}}
            return combined.get("simulation", combined)
            
        except Exception as e:
            logger.error(f"Error in rebalance simulation: {e}")
            raise
    
    def _calculate_weighted_apy(self, holdings: List[Dict], total_value: float) -> float:
        """Calculate portfolio-weighted APY"""
        if total_value == 0:
            return 0.0
        
        weighted_sum = sum(
            (holding["value_usd"] / total_value) * holding["apy"]
            for holding in holdings
        )
        
        return weighted_sum
    
    async def _apply_recommendations(
        self,
        holdings: List[Dict],
        recommendations: List[Dict]
    ) -> List[Dict]:
        """Apply rebalancing recommendations to holdings (simulation)"""
        
        # Create a copy of holdings
        simulated = [h.copy() for h in holdings]
        
        # Get protocol APYs
        protocols = await self._get_protocol_data()
        protocol_apy_map = {p["name"]: p["apy"] for p in protocols}
        
        for rec in recommendations:
            from_protocol = rec["from"]
            to_protocol = rec["to"]
            percent = rec["percent"] / 100.0
            
            # Find source holding
            from_holding = next((h for h in simulated if h["protocol"] == from_protocol), None)
            if not from_holding:
                continue
            
            # Calculate amount to move
            move_value = from_holding["value_usd"] * percent
            move_amount = from_holding["amount"] * percent
            
            # Reduce source
            from_holding["amount"] -= move_amount
            from_holding["value_usd"] -= move_value
            
            # Find or create target holding
            to_holding = next((h for h in simulated if h["protocol"] == to_protocol), None)
            if to_holding:
                to_holding["amount"] += move_amount
                to_holding["value_usd"] += move_value
            else:
                # Create new holding
                simulated.append({
                    "protocol": to_protocol,
                    "symbol": to_protocol[:4].upper(),  # Simplified
                    "amount": move_amount,
                    "value_usd": move_value,
                    "apy": protocol_apy_map.get(to_protocol, 0.0)
                })
        
        # Remove holdings with zero value
        simulated = [h for h in simulated if h["value_usd"] > 0.01]
        
        return simulated
    
    async def record_ai_decision(self, wallet_address: str, result: Dict[str, Any]):
        """
        Record AI decision in ai_decision_logs table
        
        Args:
            wallet_address: User's wallet address
            result: AI analysis result
        """
        try:
            client = self._get_supabase_client()
            
            # Get user ID
            user_response = client.table("users").select("id").eq("wallet_address", wallet_address).execute()
            if not user_response.data:
                logger.warning(f"User not found for wallet: {wallet_address}")
                return
            
            user_id = user_response.data[0]["id"]
            
            # Prepare log entry
            log_entry = {
                "user_id": user_id,
                "recommendation": {
                    "action": result.get("action"),
                    "recommendations": result.get("recommendations", []),
                    "expected_yield_increase": result.get("expected_yield_increase"),
                    "ai_model": result.get("ai_model")
                },
                "explanation": result.get("explanation"),
                "confidence": result.get("confidence"),
                "executed": False
            }
            
            # Insert into database
            client.table("ai_decision_logs").insert(log_entry).execute()
            
            logger.info(f"✓ AI decision logged for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording AI decision: {e}")
    
    async def _log_simulation(self, wallet_address: str, simulation: Dict[str, Any]):
        """Log simulation in transaction_logs table"""
        try:
            client = self._get_supabase_client()
            
            # Get user ID
            user_response = client.table("users").select("id").eq("wallet_address", wallet_address).execute()
            if not user_response.data:
                return
            
            user_id = user_response.data[0]["id"]
            
            # Log each simulated change
            for change in simulation["simulated_changes"]:
                log_entry = {
                    "user_id": user_id,
                    "transaction_type": "rebalance_simulation",
                    "from_protocol": change["from"],
                    "to_protocol": change["to"],
                    "amount": change["percent"],
                    "status": "simulated",
                    "tx_hash": None
                }
                
                client.table("transaction_logs").insert(log_entry).execute()
            
            logger.info(f"✓ Simulation logged: {len(simulation['simulated_changes'])} transactions")
            
        except Exception as e:
            logger.error(f"Error logging simulation: {e}")


# Global AI agent instance
ai_agent = AIAgent()
