"""
Portfolio Routes

API endpoints for portfolio management, holdings, and AI analysis.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Request, Query, HTTPException
from pydantic import BaseModel

from backend.services.portfolio import portfolio_service
from backend.services.ai_agent import ai_agent
from backend.core.security import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class UpdateHoldingRequest(BaseModel):
    """Request model for updating a holding"""
    wallet: str
    protocol: str
    symbol: str
    amount: float


class RiskPreferenceRequest(BaseModel):
    """Request model for updating risk preference"""
    risk_preference: str


class AddHoldingRequest(BaseModel):
    """Request model for adding a new holding"""
    wallet: str
    protocol_name: str
    symbol: str
    amount: float


class UpdateHoldingAmountRequest(BaseModel):
    """Request model for updating holding amount"""
    holding_id: int
    amount: float


class RemoveHoldingRequest(BaseModel):
    """Request model for removing a holding"""
    holding_id: int


@router.get("/")
async def get_portfolio(
    request: Request,
    wallet: str = Query(..., description="Wallet address"),
    fresh: bool = Query(False, description="Force fresh API fetch")
):
    """
    Get user portfolio with all holdings
    
    Query Parameters:
    - wallet: User's wallet address (required)
    - fresh: Force fresh API fetch (optional, default: false)
    
    Returns:
        Portfolio data with holdings and total value
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        # Log request
        print(f"[PORTFOLIO] Wallet requested: {wallet}")
        if fresh:
            print("[PORTFOLIO] Forced fresh fetch triggered")
        
        portfolio = await portfolio_service.get_user_portfolio(wallet)
        
        # Log result
        print(f"[PORTFOLIO] Portfolio query result: {portfolio}")
        
        if portfolio is None:
            # Return empty portfolio instead of 404
            print(f"[PORTFOLIO] No user found for wallet {wallet}, returning empty portfolio")
            return {
                "wallet": wallet,
                "holdings": [],
                "total_value_usd": 0,
                "message": "No tokens or holdings found"
            }
        
        # Check if portfolio has no holdings
        if not portfolio.get("holdings"):
            print(f"[PORTFOLIO] User exists but has no holdings")
            return {
                "wallet": wallet,
                "holdings": [],
                "total_value_usd": 0,
                "message": "No tokens detected in portfolio."
            }
        
        print(f"[PORTFOLIO] Returning {len(portfolio.get('holdings', []))} holdings")
        return portfolio
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to fetch portfolio", "message": str(e)}
        )


@router.post("/update")
async def update_holding(
    request: Request,
    data: UpdateHoldingRequest
):
    """
    Update a holding's amount and recalculate USD value
    
    Request Body:
    ```json
    {
      "wallet": "0xabc...",
      "protocol": "Aave",
      "symbol": "AAVE",
      "amount": 2.0
    }
    ```
    
    Returns:
        Updated portfolio data
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        portfolio = await portfolio_service.update_holding(
            wallet_address=data.wallet,
            protocol=data.protocol,
            symbol=data.symbol,
            new_amount=data.amount
        )
        
        logger.info(f"✓ Updated holding for {data.wallet}: {data.protocol} {data.symbol} = {data.amount}")
        return portfolio
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error updating holding: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update holding", "message": str(e)}
        )


@router.post("/refresh")
async def refresh_portfolio(
    request: Request,
    wallet: str = Query(..., description="Wallet address")
):
    """
    Refresh all holdings' USD values using current prices
    
    Query Parameters:
    - wallet: User's wallet address (required)
    
    Returns:
        Updated portfolio data with refreshed values
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        portfolio = await portfolio_service.refresh_portfolio_values(wallet)
        
        logger.info(f"✓ Refreshed portfolio values for {wallet}")
        return portfolio
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error refreshing portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to refresh portfolio", "message": str(e)}
        )


@router.get("/demo")
async def seed_demo_portfolio(
    request: Request,
    wallet: Optional[str] = Query(None, description="Optional wallet address for auto-sync")
):
    """
    Create demo user with sample portfolio and holdings
    
    Query Parameters:
    - wallet: Optional wallet address to create/verify user (for MetaMask auto-sync)
    
    Returns:
        Demo portfolio data
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        # If wallet provided, use it for auto-sync (create user if needed)
        if wallet:
            portfolio = await portfolio_service.seed_demo_data(wallet_address=wallet)
            logger.info(f"👛 New wallet connected: {wallet}")
            logger.info(f"🗂 User auto-created/verified in Supabase")
        else:
            portfolio = await portfolio_service.seed_demo_data()
            logger.info("✓ Demo portfolio created/retrieved")
        
        return portfolio
        
    except Exception as e:
        logger.error(f"Error seeding demo data: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to seed demo data", "message": str(e)}
        )


@router.get("/analyze")
async def analyze_portfolio_ai(
    request: Request,
    wallet: str = Query(..., description="Wallet address")
):
    """
    Analyze portfolio using AI (Gemini stub)
    
    Query Parameters:
    - wallet: User's wallet address (required)
    
    Returns:
        AI analysis stub response
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        analysis = await ai_agent.analyze_portfolio(wallet)
        
        logger.info(f"✓ AI analysis generated for {wallet}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to analyze portfolio", "message": str(e)}
        )


@router.post("/risk/{wallet}")
async def update_risk_profile(
    request: Request,
    wallet: str,
    data: RiskPreferenceRequest
):
    """
    Update user's risk preference
    
    Path Parameters:
    - wallet: User's wallet address
    
    Request Body:
    ```json
    {
      "risk_preference": "low" | "medium" | "high"
    }
    ```
    
    Returns:
        Updated user data
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        result = await portfolio_service.update_risk_preference(wallet, data.risk_preference)
        
        if not result:
            raise HTTPException(status_code=404, detail={"error": "User not found"})
        
        logger.info(f"✅ Updated risk preference for {wallet}: {data.risk_preference}")
        return result
        
    except Exception as e:
        logger.error(f"Error updating risk preference: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update risk preference", "message": str(e)}
        )


@router.post("/demo/holdings/add")
async def add_demo_holding(
    request: Request,
    data: AddHoldingRequest
):
    """
    Add a new demo holding with real-time price and APY data
    
    Request Body:
    ```json
    {
      "wallet": "0xabc...",
      "protocol_name": "Aave V3",
      "symbol": "AAVE",
      "amount": 2.5
    }
    ```
    
    Returns:
        Updated portfolio data
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        portfolio = await portfolio_service.add_demo_holding(
            wallet_address=data.wallet,
            protocol_name=data.protocol_name,
            symbol=data.symbol,
            amount=data.amount
        )
        
        if not portfolio:
            raise HTTPException(status_code=404, detail={"error": "Portfolio not found"})
        
        logger.info(f"✅ Added holding: {data.amount} {data.symbol} on {data.protocol_name}")
        return portfolio
        
    except Exception as e:
        logger.error(f"Error adding demo holding: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to add holding", "message": str(e)}
        )


@router.post("/demo/holdings/update")
async def update_demo_holding_amount(
    request: Request,
    data: UpdateHoldingAmountRequest
):
    """
    Update holding amount and recalculate value
    
    Request Body:
    ```json
    {
      "holding_id": 3,
      "amount": 4.0
    }
    ```
    
    Returns:
        Updated portfolio data
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        portfolio = await portfolio_service.update_demo_holding(
            holding_id=data.holding_id,
            amount=data.amount
        )
        
        if not portfolio:
            raise HTTPException(status_code=404, detail={"error": "Holding not found"})
        
        logger.info(f"✅ Updated holding #{data.holding_id}: {data.amount}")
        return portfolio
        
    except Exception as e:
        logger.error(f"Error updating demo holding: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to update holding", "message": str(e)}
        )


@router.post("/demo/holdings/remove")
async def remove_demo_holding(
    request: Request,
    data: RemoveHoldingRequest
):
    """
    Remove a demo holding and return updated holdings list
    
    Request Body:
    ```json
    {
      "holding_id": 3
    }
    ```
    
    Returns:
        Dict with message, updated holdings list, and total_value
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        result = await portfolio_service.remove_demo_holding(holding_id=data.holding_id)
        
        logger.info(f"✅ Removed holding #{data.holding_id}")
        return result
        
    except ValueError as ve:
        # Holding not found
        logger.error(f"Holding not found: {data.holding_id}")
        raise HTTPException(
            status_code=404,
            detail={"error": "Holding not found", "message": str(ve)}
        )
    except Exception as e:
        logger.error(f"Error removing demo holding: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to remove holding", "message": str(e)}
        )
