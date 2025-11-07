"""
Portfolio Service

Manages user portfolios, holdings, and USD value calculations.
Integrates with Supabase for data persistence and CoinGecko for live pricing.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp
from datetime import datetime

from backend.core.config import settings
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# CoinGecko token ID mapping
COINGECKO_TOKEN_MAP = {
    "AAVE": "aave",
    "stETH": "lido-dao",
    "ETH": "ethereum",
    "WETH": "ethereum",
    "CRV": "curve-dao-token",
    "UNI": "uniswap",
    "COMP": "compound-governance-token",
    "DAI": "dai",
    "USDC": "usd-coin",
    "USDT": "tether"
}


class PortfolioService:
    """Service for managing user portfolios and holdings"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self.supabase is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Supabase credentials not configured")
            self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("✓ Supabase client initialized for portfolio service")
        return self.supabase
    
    async def get_token_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch current USD prices from CoinGecko
        
        Args:
            symbols: List of token symbols (e.g., ["AAVE", "stETH"])
            
        Returns:
            Dict mapping symbol to USD price
        """
        # Map symbols to CoinGecko IDs
        token_ids = []
        symbol_to_id = {}
        
        for symbol in symbols:
            coingecko_id = COINGECKO_TOKEN_MAP.get(symbol.upper())
            if coingecko_id:
                token_ids.append(coingecko_id)
                symbol_to_id[symbol] = coingecko_id
            else:
                logger.warning(f"No CoinGecko mapping for symbol: {symbol}")
        
        if not token_ids:
            return {}
        
        # Fetch prices from CoinGecko
        try:
            url = f"{settings.COINGECKO_URL}/simple/price"
            params = {
                "ids": ",".join(token_ids),
                "vs_currencies": "usd"
            }
            
            headers = {}
            if settings.COINGECKO_API_KEY:
                headers["x-cg-demo-api-key"] = settings.COINGECKO_API_KEY
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"CoinGecko API error: {response.status}")
                        print(f"[COINGECKO] API error: Status {response.status}")
                        return {}
                    
                    data = await response.json()
                    
                    # Log raw response (first 2 items only)
                    print(f"[COINGECKO] Raw price response: {dict(list(data.items())[:2])}")
                    
                    # Map back to symbols
                    prices = {}
                    for symbol, coingecko_id in symbol_to_id.items():
                        if coingecko_id in data and "usd" in data[coingecko_id]:
                            prices[symbol] = float(data[coingecko_id]["usd"])
                    
                    print(f"[COINGECKO] Fetched {len(prices)} prices: {prices}")
                    logger.info(f"✓ Fetched {len(prices)} token prices from CoinGecko")
                    return prices
                    
        except Exception as e:
            logger.error(f"Error fetching token prices: {e}")
            return {}
    
    async def get_user_portfolio(self, wallet_address: str) -> Dict[str, Any]:
        """
        Fetch user portfolio with all holdings
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            Portfolio data with holdings
        """
        try:
            print(f"[PORTFOLIO-SERVICE] Querying portfolio for wallet: {wallet_address}")
            
            client = self._get_supabase_client()
            
            # Get user
            user_response = client.table("users").select("*").eq("wallet_address", wallet_address).execute()
            
            print(f"[PORTFOLIO-SERVICE] User query returned {len(user_response.data)} results")
            
            if not user_response.data:
                logger.warning(f"User not found: {wallet_address}")
                print(f"[PORTFOLIO-SERVICE] No user found in database for {wallet_address}")
                return None
            
            user = user_response.data[0]
            user_id = user["id"]
            
            # Get portfolio
            portfolio_response = client.table("portfolios").select("*").eq("user_id", user_id).execute()
            
            if not portfolio_response.data:
                # Create portfolio if doesn't exist
                portfolio_data = {
                    "user_id": user_id,
                    "total_value": 0
                }
                portfolio_response = client.table("portfolios").insert(portfolio_data).execute()
                portfolio = portfolio_response.data[0]
            else:
                portfolio = portfolio_response.data[0]
            
            portfolio_id = portfolio["id"]
            
            # Get holdings
            holdings_response = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).execute()
            
            print(f"[PORTFOLIO-SERVICE] Holdings query returned {len(holdings_response.data)} results")
            
            holdings_list = []
            for holding in holdings_response.data:
                holdings_list.append({
                    "id": holding["id"],  # ✅ Include ID for delete operations
                    "protocol": holding["protocol_name"],
                    "symbol": holding["token_symbol"],
                    "amount": float(holding["amount"]),
                    "value_usd": float(holding["value_usd"]),
                    "apy": float(holding["apy"]) if holding["apy"] else 0.0
                })
            
            result = {
                "user_id": user_id,
                "wallet_address": wallet_address,
                "risk_preference": user["risk_preference"],
                "total_value_usd": float(portfolio["total_value"]),
                "holdings": holdings_list
            }
            
            print(f"[PORTFOLIO-SERVICE] Returning portfolio with {len(holdings_list)} holdings, total value: ${result['total_value_usd']:.2f}")
            logger.info(f"✓ Retrieved portfolio for {wallet_address}: {len(holdings_list)} holdings")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            raise
    
    async def update_holding(
        self,
        wallet_address: str,
        protocol: str,
        symbol: str,
        new_amount: float
    ) -> Dict[str, Any]:
        """
        Update a holding's amount and recalculate USD value
        
        Args:
            wallet_address: User's wallet address
            protocol: Protocol name (e.g., "Aave")
            symbol: Token symbol (e.g., "AAVE")
            new_amount: New token amount
            
        Returns:
            Updated portfolio data
        """
        try:
            client = self._get_supabase_client()
            
            # Get user and portfolio
            user_response = client.table("users").select("*").eq("wallet_address", wallet_address).execute()
            if not user_response.data:
                raise ValueError(f"User not found: {wallet_address}")
            
            user_id = user_response.data[0]["id"]
            
            portfolio_response = client.table("portfolios").select("*").eq("user_id", user_id).execute()
            if not portfolio_response.data:
                raise ValueError(f"Portfolio not found for user: {wallet_address}")
            
            portfolio_id = portfolio_response.data[0]["id"]
            
            # Get current price
            prices = await self.get_token_prices([symbol])
            price = prices.get(symbol, 0.0)
            
            if price == 0.0:
                logger.warning(f"Could not fetch price for {symbol}, using 0")
            
            value_usd = new_amount * price
            
            # Get APY from protocol_data
            protocol_response = client.table("protocol_data").select("apy").eq("protocol_name", protocol).execute()
            apy = float(protocol_response.data[0]["apy"]) if protocol_response.data else 0.0
            
            # Check if holding exists
            holding_response = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).eq("protocol_name", protocol).eq("token_symbol", symbol).execute()
            
            if holding_response.data:
                # Update existing holding
                holding_id = holding_response.data[0]["id"]
                update_data = {
                    "amount": new_amount,
                    "value_usd": value_usd,
                    "apy": apy,
                    "updated_at": datetime.utcnow().isoformat()
                }
                client.table("holdings").update(update_data).eq("id", holding_id).execute()
                logger.info(f"✓ Updated holding: {protocol} {symbol} = {new_amount}")
            else:
                # Create new holding
                holding_data = {
                    "portfolio_id": portfolio_id,
                    "protocol_name": protocol,
                    "token_symbol": symbol,
                    "amount": new_amount,
                    "value_usd": value_usd,
                    "apy": apy
                }
                client.table("holdings").insert(holding_data).execute()
                logger.info(f"✓ Created new holding: {protocol} {symbol} = {new_amount}")
            
            # Recalculate total portfolio value
            await self._recalculate_portfolio_value(portfolio_id)
            
            # Return updated portfolio
            return await self.get_user_portfolio(wallet_address)
            
        except Exception as e:
            logger.error(f"Error updating holding: {e}")
            raise
    
    async def _recalculate_portfolio_value(self, portfolio_id: int):
        """Recalculate and update total portfolio value"""
        try:
            client = self._get_supabase_client()
            
            # Sum all holdings
            holdings_response = client.table("holdings").select("value_usd").eq("portfolio_id", portfolio_id).execute()
            
            total_value = sum(float(h["value_usd"]) for h in holdings_response.data)
            
            # Update portfolio
            client.table("portfolios").update({
                "total_value": total_value,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", portfolio_id).execute()
            
            logger.info(f"✓ Recalculated portfolio value: ${total_value:.2f}")
            
        except Exception as e:
            logger.error(f"Error recalculating portfolio value: {e}")
            raise
    
    async def refresh_portfolio_values(self, wallet_address: str) -> Dict[str, Any]:
        """
        Refresh USD values for all holdings using current prices
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            Updated portfolio data
        """
        try:
            client = self._get_supabase_client()
            
            # Get user and portfolio
            user_response = client.table("users").select("*").eq("wallet_address", wallet_address).execute()
            if not user_response.data:
                raise ValueError(f"User not found: {wallet_address}")
            
            user_id = user_response.data[0]["id"]
            
            portfolio_response = client.table("portfolios").select("*").eq("user_id", user_id).execute()
            if not portfolio_response.data:
                raise ValueError(f"Portfolio not found for user: {wallet_address}")
            
            portfolio_id = portfolio_response.data[0]["id"]
            
            # Get all holdings
            holdings_response = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).execute()
            
            if not holdings_response.data:
                logger.info(f"No holdings to refresh for {wallet_address}")
                return await self.get_user_portfolio(wallet_address)
            
            # Get all unique symbols
            symbols = list(set(h["token_symbol"] for h in holdings_response.data))
            
            # Fetch current prices
            prices = await self.get_token_prices(symbols)
            
            # Update each holding
            for holding in holdings_response.data:
                symbol = holding["token_symbol"]
                amount = float(holding["amount"])
                price = prices.get(symbol, 0.0)
                new_value = amount * price
                
                client.table("holdings").update({
                    "value_usd": new_value,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", holding["id"]).execute()
            
            logger.info(f"✓ Refreshed {len(holdings_response.data)} holdings for {wallet_address}")
            
            # Recalculate total
            await self._recalculate_portfolio_value(portfolio_id)
            
            # Return updated portfolio
            return await self.get_user_portfolio(wallet_address)
            
        except Exception as e:
            logger.error(f"Error refreshing portfolio values: {e}")
            raise
    
    async def seed_demo_data(self, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Create demo user with sample portfolio and holdings
        
        Args:
            wallet_address: Optional wallet address (for MetaMask auto-sync)
        
        Returns:
            Created portfolio data
        """
        try:
            print(f"[SEED-DEMO] Starting demo data seed for wallet: {wallet_address}")
            
            client = self._get_supabase_client()
            
            # Use provided wallet or default demo wallet
            demo_wallet = wallet_address or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            
            # IMPORTANT: Isolate demo wallet from real wallets
            if wallet_address and wallet_address != "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb":
                print(f"[SEED-DEMO] Real wallet detected: {wallet_address}, creating user without demo holdings")
                # For real wallets, just create user if needed, don't add demo holdings
                user_response = client.table("users").select("*").eq("wallet_address", wallet_address).execute()
                if not user_response.data:
                    user_data = {
                        "wallet_address": wallet_address,
                        "risk_preference": "medium"
                    }
                    user_response = client.table("users").insert(user_data).execute()
                    print(f"[SEED-DEMO] Created user for real wallet: {wallet_address}")
                
                # Return empty portfolio for real wallets
                return {
                    "wallet": wallet_address,
                    "holdings": [],
                    "total_value_usd": 0,
                    "message": "User created. Add holdings to get started."
                }
            
            print(f"[SEED-DEMO] Demo wallet detected: {demo_wallet}, loading sample data")
            
            # Check if user exists
            user_response = client.table("users").select("*").eq("wallet_address", demo_wallet).execute()
            
            if not user_response.data:
                # Create demo user
                user_data = {
                    "wallet_address": demo_wallet,
                    "risk_preference": "medium"
                }
                user_response = client.table("users").insert(user_data).execute()
                logger.info(f"✓ Created demo user: {demo_wallet}")
            
            user_id = user_response.data[0]["id"]
            
            # Check if portfolio exists
            portfolio_response = client.table("portfolios").select("*").eq("user_id", user_id).execute()
            
            if not portfolio_response.data:
                portfolio_data = {
                    "user_id": user_id,
                    "total_value": 0
                }
                portfolio_response = client.table("portfolios").insert(portfolio_data).execute()
                logger.info(f"✓ Created demo portfolio")
            
            portfolio_id = portfolio_response.data[0]["id"]
            
            # Check if holdings exist
            holdings_response = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).execute()
            
            if not holdings_response.data:
                # Get current prices
                prices = await self.get_token_prices(["AAVE", "stETH"])
                
                # Create demo holdings
                demo_holdings = [
                    {
                        "portfolio_id": portfolio_id,
                        "protocol_name": "Aave",
                        "token_symbol": "AAVE",
                        "amount": 2.0,
                        "value_usd": 2.0 * prices.get("AAVE", 100.0),
                        "apy": 4.12
                    },
                    {
                        "portfolio_id": portfolio_id,
                        "protocol_name": "Lido",
                        "token_symbol": "stETH",
                        "amount": 0.8,
                        "value_usd": 0.8 * prices.get("stETH", 2300.0),
                        "apy": 5.24
                    }
                ]
                
                client.table("holdings").insert(demo_holdings).execute()
                logger.info(f"✓ Created {len(demo_holdings)} demo holdings")
                
                # Recalculate total
                await self._recalculate_portfolio_value(portfolio_id)
            
            # Return portfolio
            return await self.get_user_portfolio(demo_wallet)
            
        except Exception as e:
            logger.error(f"Error seeding demo data: {e}")
            raise
    
    async def update_risk_preference(self, wallet_address: str, risk: str) -> Dict[str, Any]:
        """
        Update user's risk preference
        
        Args:
            wallet_address: Wallet address
            risk: Risk level (low, medium, high)
            
        Returns:
            Updated user data
        """
        try:
            client = self._get_supabase_client()
            
            # Check if user exists
            user_response = client.table("users").select("id").eq("wallet_address", wallet_address).execute()
            
            if not user_response.data:
                logger.warning(f"User not found for wallet: {wallet_address}")
                return None
            
            # Update risk preference
            update_response = client.table("users").update({
                "risk_preference": risk
            }).eq("wallet_address", wallet_address).execute()
            
            logger.info(f"✅ Updated risk preference for {wallet_address}: {risk}")
            
            return {
                "wallet": wallet_address,
                "risk_preference": risk
            }
            
        except Exception as e:
            logger.error(f"Error updating risk preference: {e}")
            raise
    
    async def add_demo_holding(
        self,
        wallet_address: str,
        protocol_name: str,
        symbol: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Add a new demo holding using protocol_market_data table
        
        Args:
            wallet_address: Wallet address
            protocol_name: Protocol name (e.g., "Aave")
            symbol: Token symbol (e.g., "AAVE")
            amount: Token amount
            
        Returns:
            Updated portfolio
        """
        try:
            client = self._get_supabase_client()
            
            # Step 1: Get user_id from wallet_address
            user_response = client.table("users").select("id").eq("wallet_address", wallet_address).execute()
            
            if not user_response.data:
                logger.error(f"No user found for wallet: {wallet_address}")
                raise ValueError(f"No user found for wallet {wallet_address}")
            
            user_id = user_response.data[0]["id"]
            
            # Step 2: Get portfolio_id from user_id (or create if doesn't exist)
            portfolio_response = client.table("portfolios").select("id").eq("user_id", user_id).execute()
            
            if not portfolio_response.data:
                # Create new portfolio if none exists
                logger.info(f"Creating new portfolio for user_id: {user_id}")
                new_portfolio = client.table("portfolios").insert({
                    "user_id": user_id,
                    "total_value": 0
                }).execute()
                portfolio_id = new_portfolio.data[0]["id"]
            else:
                portfolio_id = portfolio_response.data[0]["id"]
            
            # Step 3: Fetch token data from protocol_market_data table
            token_response = client.table("protocol_market_data").select("*").or_(
                f"symbol.eq.{symbol.upper()},protocol_name.ilike.%{protocol_name}%"
            ).execute()
            
            if not token_response.data:
                logger.error(f"Protocol/token not found in market data: {protocol_name}/{symbol}")
                raise ValueError(f"Protocol {protocol_name} or token {symbol} not found in market data")
            
            # Use the first matching token
            token = token_response.data[0]
            price_usd = float(token.get("price_usd", 0))
            apy = float(token.get("apy", 0))
            value_usd = round(price_usd * amount, 2)
            
            # Step 4: Insert holding
            holding_data = {
                "portfolio_id": portfolio_id,
                "protocol_name": token["protocol_name"],
                "token_symbol": token["symbol"],
                "amount": amount,
                "value_usd": value_usd,
                "apy": apy,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            client.table("holdings").insert(holding_data).execute()
            
            # Step 5: Recalculate portfolio total value
            await self._recalculate_portfolio_value(portfolio_id)
            
            logger.info(f"✅ Added holding: {amount} {symbol} on {token['protocol_name']} (price: ${price_usd}, APY: {apy}%, value: ${value_usd})")
            
            # Return updated portfolio
            return await self.get_user_portfolio(wallet_address)
            
        except Exception as e:
            logger.error(f"Error adding demo holding: {e}")
            raise
    
    async def update_demo_holding(
        self,
        holding_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Update holding amount and recalculate value using protocol_market_data table
        
        Args:
            holding_id: Holding ID
            amount: New amount
            
        Returns:
            Updated portfolio
        """
        try:
            client = self._get_supabase_client()
            
            # Get holding details
            holding_response = client.table("holdings").select("id, token_symbol, portfolio_id").eq("id", holding_id).execute()
            
            if not holding_response.data:
                logger.error(f"Holding not found: {holding_id}")
                raise ValueError(f"Holding not found: {holding_id}")
            
            holding = holding_response.data[0]
            symbol = holding["token_symbol"]
            portfolio_id = holding["portfolio_id"]
            
            # Fetch updated price and APY from protocol_market_data table
            token_response = client.table("protocol_market_data").select("price_usd, apy").eq("symbol", symbol.upper()).execute()
            
            if not token_response.data:
                logger.error(f"Token not found in market data: {symbol}")
                raise ValueError(f"Token {symbol} not found in market data")
            
            price_usd = float(token_response.data[0]["price_usd"])
            apy = float(token_response.data[0]["apy"])
            value_usd = round(price_usd * amount, 2)
            
            # Update holding
            client.table("holdings").update({
                "amount": amount,
                "value_usd": value_usd,
                "apy": apy,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", holding_id).execute()
            
            # Recalculate portfolio total value
            holdings_response = client.table("holdings").select("value_usd").eq("portfolio_id", portfolio_id).execute()
            total_value = sum(float(h["value_usd"]) for h in holdings_response.data)
            
            client.table("portfolios").update({
                "total_value": total_value
            }).eq("id", portfolio_id).execute()
            
            logger.info(f"✅ Updated holding #{holding_id}: {amount} {symbol} (new value: ${value_usd:.2f}, portfolio total: ${total_value:.2f})")
            
            # Get updated holdings list
            updated_holdings = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).execute()
            
            return {
                "message": "Holding updated",
                "holdings": updated_holdings.data,
                "total_value": total_value
            }
            
        except Exception as e:
            logger.error(f"Error updating demo holding: {e}")
            raise
    
    async def remove_demo_holding(self, holding_id: int) -> Dict[str, Any]:
        """
        Remove a demo holding and return updated holdings list
        
        Args:
            holding_id: Holding ID
            
        Returns:
            Dict with message, updated holdings list, and total_value
        """
        client = self._get_supabase_client()
        
        logger.info(f"[REMOVE-HOLDING] Starting removal of holding #{holding_id}")
        
        # Step 1: Fetch holding to get portfolio_id
        holding_response = client.table("holdings").select("id, portfolio_id").eq("id", holding_id).execute()
        
        logger.info(f"[REMOVE-HOLDING] Query result: {holding_response.data}")
        
        if not holding_response.data or len(holding_response.data) == 0:
            logger.error(f"[REMOVE-HOLDING] Holding not found: {holding_id}")
            raise ValueError(f"Holding {holding_id} not found")
        
        portfolio_id = holding_response.data[0]["portfolio_id"]
        logger.info(f"[REMOVE-HOLDING] Found holding in portfolio {portfolio_id}")
        
        # Step 2: Delete holding from Supabase
        try:
            delete_response = client.table("holdings").delete().eq("id", holding_id).execute()
            logger.info(f"[REMOVE-HOLDING] Delete response: {delete_response}")
            logger.info(f"✅ Deleted holding #{holding_id} from database")
        except Exception as delete_error:
            logger.error(f"[REMOVE-HOLDING] Delete failed: {delete_error}")
            raise Exception(f"Failed to delete holding: {str(delete_error)}")
        
        # Step 3: Recalculate portfolio total value
        holdings_response = client.table("holdings").select("value_usd").eq("portfolio_id", portfolio_id).execute()
        
        # Handle empty holdings (all deleted)
        if holdings_response.data and len(holdings_response.data) > 0:
            total_value = sum(float(h["value_usd"]) for h in holdings_response.data)
        else:
            total_value = 0.0
            logger.info(f"[REMOVE-HOLDING] No holdings remaining for portfolio {portfolio_id}")
        
        # Update portfolio total
        client.table("portfolios").update({
            "total_value": total_value
        }).eq("id", portfolio_id).execute()
        
        logger.info(f"✅ Removed holding #{holding_id} (portfolio total: ${total_value:.2f})")
        
        # Step 4: Fetch updated holdings list
        updated_holdings_response = client.table("holdings").select("*").eq("portfolio_id", portfolio_id).execute()
        updated_holdings = updated_holdings_response.data if updated_holdings_response.data else []
        
        logger.info(f"[REMOVE-HOLDING] Returning {len(updated_holdings)} holdings")
        
        return {
            "message": f"Holding {holding_id} removed successfully",
            "holdings": updated_holdings,
            "total_value": total_value
        }


# Global service instance
portfolio_service = PortfolioService()
