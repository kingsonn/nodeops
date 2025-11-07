"""
AI Routes

API endpoints for AI-powered portfolio analysis and rebalancing simulation.
"""

import logging
from fastapi import APIRouter, Request, Query, HTTPException
from pydantic import BaseModel

from backend.services.ai_agent import ai_agent
from backend.core.security import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ExecuteRequest(BaseModel):
    """Request model for executing a recommendation"""
    wallet: str
    decision_id: int


@router.get("/analyze")
async def analyze_portfolio(
    request: Request,
    wallet: str = Query(..., description="Wallet address")
):
    """
    Analyze portfolio and generate AI-powered rebalancing recommendations
    
    Query Parameters:
    - wallet: User's wallet address (required)
    
    Returns:
        AI analysis with recommendations, confidence, and explanation
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        logger.info(f"🤖 AI analysis requested for wallet: {wallet}")
        
        analysis = await ai_agent.analyze_portfolio(wallet)
        
        logger.info(f"✓ AI analysis complete for {wallet}")
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to analyze portfolio", "message": str(e)}
        )


@router.get("/simulate")
async def simulate_rebalance(
    request: Request,
    wallet: str = Query(..., description="Wallet address")
):
    """
    Simulate rebalancing based on AI recommendations
    
    Query Parameters:
    - wallet: User's wallet address (required)
    
    Returns:
        Simulation results with before/after APY and expected gains
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    try:
        logger.info(f"🎯 Rebalance simulation requested for wallet: {wallet}")
        
        simulation = await ai_agent.simulate_rebalance(wallet)
        
        logger.info(f"✓ Simulation complete for {wallet}")
        return simulation
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to simulate rebalance", "message": str(e)}
        )


@router.post("/execute")
async def execute_recommendation(
    request: Request,
    data: ExecuteRequest
):
    """
    Mark a recommendation as executed (stub for future on-chain implementation)
    
    Request Body:
    ```json
    {
      "wallet": "0xabc...",
      "decision_id": 123
    }
    ```
    
    Returns:
        Execution status (currently a stub)
    """
    try:
        check_rate_limit(request)
    except HTTPException as e:
        raise e
    
    logger.info(f"⚠️  Execute endpoint called (stub) for wallet: {data.wallet}, decision: {data.decision_id}")
    
    # This is a stub - real implementation would:
    # 1. Verify the decision exists
    # 2. Generate on-chain transactions
    # 3. Submit to blockchain
    # 4. Update ai_decision_logs.executed = True
    
    return {
        "status": "stub",
        "message": "Execution endpoint not yet implemented - no on-chain transactions will occur",
        "wallet": data.wallet,
        "decision_id": data.decision_id,
        "note": "This is a simulation-only system. Real DeFi transactions require on-chain integration."
    }
