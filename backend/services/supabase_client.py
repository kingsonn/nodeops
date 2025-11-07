"""
Shared Supabase Client

Provides a singleton Supabase client instance for all services.
"""

import logging
from supabase import create_client, Client
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Singleton Supabase client
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton"""
    global _supabase_client
    
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured")
        
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("✓ Supabase client initialized")
    
    return _supabase_client


# Export singleton instance for direct import
supabase = get_supabase_client()
