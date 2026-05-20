"""
Rate limiting middleware using slowapi (Starlette-compatible).
Backed by Redis for distributed rate limiting across multiple workers.
Falls back to in-memory if Redis is unavailable.
"""
import os
import logging
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

RATE_LIMIT_STORAGE = os.getenv(
    "RATE_LIMIT_STORAGE_URL", "memory://"
)

def _get_storage_uri() -> str:
    """Try Redis; fall back to in-memory if not configured."""
    url = os.getenv("RATE_LIMIT_STORAGE_URL", "")
    if url and url.startswith("redis://"):
        return url
    logger.warning("Rate limiter: Redis not configured, using in-memory storage (not distributed)")
    return "memory://"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_storage_uri(),
    default_limits=["300/minute"],
)

# Export the 429 handler for registration in main.py
rate_limit_exceeded_handler = _rate_limit_exceeded_handler
