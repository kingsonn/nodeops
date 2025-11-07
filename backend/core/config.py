"""
Configuration Management

Loads and validates environment variables for AutoDeFi.AI
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFILLAMA_API_KEY: str = os.getenv("DEFILLAMA_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Backend Configuration
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    # AI Agent Configuration
    AI_MODEL: str = os.getenv("AI_MODEL", "llama-3.1-70b-versatile")
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.3"))
    FALLBACK_TO_RULE_ENGINE: bool = os.getenv("FALLBACK_TO_RULE_ENGINE", "true").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # External APIs
    DEFI_LLAMA_URL: str = os.getenv("DEFI_LLAMA_URL", "https://yields.llama.fi/pools")
    COINGECKO_URL: str = os.getenv("COINGECKO_URL", "https://api.coingecko.com/api/v3")
    
    # Caching
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "900"))  # 15 minutes default
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "60"))
    
    # Vault Scheduler
    VAULT_UPDATE_INTERVAL_HOURS: int = int(os.getenv("VAULT_UPDATE_INTERVAL_HOURS", "6"))
    VAULT_REFRESH_ON_STARTUP: bool = os.getenv("VAULT_REFRESH_ON_STARTUP", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


# Log configuration status
def log_config_status():
    """Log configuration status for debugging"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=== AutoDeFi.AI Configuration ===")
    logger.info(f"Backend Port: {settings.BACKEND_PORT}")
    logger.info(f"AI Model: {settings.AI_MODEL}")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL[:30]}..." if settings.SUPABASE_URL else "Not configured")
    logger.info(f"Gemini API Key: {'✓ Configured' if settings.GEMINI_API_KEY else '✗ Missing'}")
    logger.info(f"Groq API Key: {'✓ Configured' if settings.GROQ_API_KEY else '✗ Missing'}")
    logger.info(f"CoinGecko API Key: {'✓ Configured' if settings.COINGECKO_API_KEY else '✗ Missing'}")
    logger.info(f"Cache TTL: {settings.CACHE_TTL}s")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT} req/min")
    logger.info("=================================")
