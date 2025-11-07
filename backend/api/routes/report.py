"""
Report API Routes
Generates downloadable PDF audit reports for AI analysis
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import logging

from backend.services.report_service import report_service

router = APIRouter(prefix="/api/report", tags=["report"])
logger = logging.getLogger(__name__)


@router.get("/generate")
async def generate_audit_report(
    wallet: str = Query(..., description="Wallet address to generate report for")
) -> StreamingResponse:
    """
    Generate AI Portfolio Audit Report PDF
    
    Args:
        wallet: Wallet address (e.g., 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb)
        
    Returns:
        PDF file download
        
    Example:
        GET /api/report/generate?wallet=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
    """
    try:
        logger.info(f"[REPORT-API] 📡 Generating report for wallet: {wallet[:10]}...")
        
        if not wallet or len(wallet) < 10:
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        report = await report_service.generate_analysis_report(wallet)
        
        logger.info(f"[REPORT-API] ✅ Report generated successfully")
        return report
    
    except Exception as e:
        logger.error(f"[REPORT-API] ❌ Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate audit report: {str(e)}"
        )


@router.get("/vault/{vault_id}")
async def generate_vault_report(vault_id: int) -> StreamingResponse:
    """
    Generate AI Vault Audit Report PDF
    
    Args:
        vault_id: Vault ID to generate report for
        
    Returns:
        PDF file download
        
    Example:
        GET /api/report/vault/1
    """
    try:
        logger.info(f"[REPORT-API] 📡 Generating vault report for vault #{vault_id}...")
        
        report = await report_service.generate_vault_report(vault_id)
        
        logger.info(f"[REPORT-API] ✅ Vault report generated successfully")
        return report
    
    except Exception as e:
        logger.error(f"[REPORT-API] ❌ Error generating vault report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate vault report: {str(e)}"
        )


@router.get("/test")
async def test_report_service():
    """
    Test endpoint to verify report service is working
    
    Returns:
        Status message
    """
    return {
        "status": "ok",
        "message": "Report service is operational",
        "endpoints": {
            "portfolio_report": "/api/report/generate?wallet=<address>",
            "vault_report": "/api/report/vault/<vault_id>"
        }
    }
