"""
Async Redis cache for AI inference results.
Prevents redundant model inference on duplicate or near-duplicate complaints.
"""
import hashlib
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

REDIS_URL          = os.getenv("REDIS_URL", "redis://localhost:6379/0")
INFERENCE_TTL      = int(os.getenv("REDIS_INFERENCE_TTL", "3600"))  # 1 hour


class RedisCache:
    def __init__(self):
        self._client = None

    async def _get_client(self):
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                await self._client.ping()
                logger.info("Redis cache: connection established")
            except Exception as e:
                logger.warning(f"Redis cache: connection failed ({e}). Caching disabled.")
                self._client = None
        return self._client

    @staticmethod
    def _text_hash(text: str) -> str:
        """Stable SHA-256 hash of complaint text — used as cache key."""
        return "inference:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def get_inference(self, text: str) -> Optional[dict]:
        """Return cached inference result or None if miss / Redis down."""
        try:
            client = await self._get_client()
            if not client:
                return None
            key   = self._text_hash(text)
            value = await client.get(key)
            if value:
                logger.debug(f"Inference cache HIT for key {key[:20]}...")
                return json.loads(value)
            logger.debug(f"Inference cache MISS for key {key[:20]}...")
            return None
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    async def set_inference(self, text: str, result: dict, ttl: int = INFERENCE_TTL) -> bool:
        """Cache inference result. Returns True if stored, False on failure."""
        try:
            client = await self._get_client()
            if not client:
                return False
            key = self._text_hash(text)
            await client.set(key, json.dumps(result), ex=ttl)
            logger.debug(f"Inference cached for key {key[:20]}... (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            return False

    async def get_rate_limit_count(self, key: str) -> int:
        """Retrieve current rate limit counter value."""
        try:
            client = await self._get_client()
            if not client:
                return 0
            val = await client.get(f"rl:{key}")
            return int(val) if val else 0
        except Exception:
            return 0

    async def ping(self) -> bool:
        """Health check — returns True if Redis is reachable."""
        try:
            client = await self._get_client()
            if not client:
                return False
            await client.ping()
            return True
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None


# Singleton
redis_cache = RedisCache()
