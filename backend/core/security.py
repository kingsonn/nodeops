"""
Security Utilities

Rate limiting and security middleware for AutoDeFi.AI
"""

import time
import logging
from typing import Dict
from collections import defaultdict
from fastapi import Request, HTTPException

from backend.core.config import settings

logger = logging.getLogger(__name__)

# In-memory rate limiter storage
# Format: {ip_address: [(timestamp1, timestamp2, ...)]}
_rate_limit_storage: Dict[str, list] = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded IP first (for proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Fall back to direct connection IP
    if request.client:
        return request.client.host
    
    return "unknown"


def check_rate_limit(request: Request, limit: int = None, window: int = 60) -> None:
    """
    Check if request exceeds rate limit
    
    Args:
        request: FastAPI request object
        limit: Maximum requests per window (default from settings)
        window: Time window in seconds (default 60)
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if limit is None:
        limit = settings.RATE_LIMIT_PER_MINUTE
    
    client_ip = get_client_ip(request)
    current_time = time.time()
    
    # Get request history for this IP
    request_times = _rate_limit_storage[client_ip]
    
    # Remove timestamps outside the window
    cutoff_time = current_time - window
    request_times[:] = [t for t in request_times if t > cutoff_time]
    
    # Check if limit exceeded
    if len(request_times) >= limit:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail={"error": "Rate limit exceeded. Try again later."}
        )
    
    # Add current request timestamp
    request_times.append(current_time)
    
    # Clean up old IPs periodically (keep last 1000 IPs)
    if len(_rate_limit_storage) > 1000:
        # Remove oldest entries
        sorted_ips = sorted(
            _rate_limit_storage.items(),
            key=lambda x: max(x[1]) if x[1] else 0
        )
        for ip, _ in sorted_ips[:500]:
            del _rate_limit_storage[ip]


def get_rate_limit_stats() -> Dict[str, int]:
    """Get current rate limit statistics"""
    return {
        "tracked_ips": len(_rate_limit_storage),
        "total_requests": sum(len(times) for times in _rate_limit_storage.values())
    }
