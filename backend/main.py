"""
FastAPI Backend Entry Point for AutoDeFi.AI

This is the main application file that initializes the FastAPI server
and registers all API routes.

Features:
- DeFi protocol data aggregation from DeFiLlama and CoinGecko
- Supabase database integration
- In-memory caching with TTL
- Rate limiting
- AI agent integration (Gemini - stub for future use)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from dotenv import load_dotenv

from backend.core.config import settings, log_config_status
from backend.api.routes import data, portfolio, ai, vaults, alerts, report
from backend.tasks.vault_scheduler import start_vault_scheduler, stop_vault_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AutoDeFi.AI API",
    description="AI-powered DeFi portfolio optimizer backend",
    version="0.1.0"
)

# ✅ CORS Configuration (MUST come before router registration)
# Allow requests from Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3000",
    "https://autodefi.ai",  # Future production deployment
]

# Add any additional origins from environment variable
if settings.CORS_ORIGINS:
    env_origins = settings.CORS_ORIGINS.split(",")
    origins.extend([origin.strip() for origin in env_origins if origin.strip() not in origins])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Strong Global CORS Enforcer - Guarantees headers on ALL responses
@app.middleware("http")
async def global_cors_enforcer(request, call_next):
    """
    Force CORS headers on every response, including errors and custom responses.
    This ensures /api/alerts and all other routes always have CORS headers.
    """
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response = JSONResponse({"message": "CORS preflight OK"})
    else:
        response = await call_next(request)
    
    # Force CORS headers on ALL responses (errors, JSON, custom responses)
    origin = request.headers.get("origin", "http://localhost:3000")
    
    # Use specific origin if in allowed list, otherwise use localhost:3000 for dev
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

logger.info(f"✓ CORS enabled for origins: {origins}")
# ---------------------------

# Register routers
app.include_router(data.router)
app.include_router(portfolio.router)
app.include_router(ai.router)
app.include_router(vaults.router)
app.include_router(alerts.router)
app.include_router(report.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=== AutoDeFi.AI Backend Starting ===")
    log_config_status()
    
    # Groq API initialization
    if settings.GROQ_API_KEY:
        logger.info(f"✓ Groq API initialized (Model: {settings.AI_MODEL})")
    else:
        logger.warning("✗ Groq API key not configured")
    
    # Start vault auto-refresh scheduler
    try:
        start_vault_scheduler()
        logger.info("✓ Vault scheduler started")
    except Exception as e:
        logger.error(f"✗ Failed to start vault scheduler: {e}")
    
    logger.info("=== Backend Ready ===")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("=== AutoDeFi.AI Backend Shutting Down ===")
    
    # Stop vault scheduler
    try:
        stop_vault_scheduler()
        logger.info("✓ Vault scheduler stopped")
    except Exception as e:
        logger.error(f"✗ Failed to stop vault scheduler: {e}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: Status and version information
    """
    return {
        "status": "healthy",
        "service": "AutoDeFi.AI Backend",
        "version": "0.1.0"
    }

@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: Welcome message and available endpoints
    """
    return {
        "message": "Welcome to AutoDeFi.AI API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/api/test-cors")
async def test_cors():
    """
    CORS test endpoint to verify cross-origin requests are working.
    
    Returns:
        dict: Success message
    """
    return {
        "message": "CORS working!",
        "status": "success",
        "origin_allowed": True
    }

# Future route imports will go here:
# from backend.api.routes import data, portfolio, start_agent, simulate_tx, history, admin

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
