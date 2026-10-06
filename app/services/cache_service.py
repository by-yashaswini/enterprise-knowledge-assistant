import hashlib
import json
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as redis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CacheService:
    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    def make_key(self, question: str, role: str, user_id: UUID) -> str:
        """
        Authorization-safe cache key.
        Includes role + user_id so one user's result can never be served
        to another user with different permissions.
        """
        normalized = question.strip().lower()
        raw = f"{role}:{user_id}:{normalized}"
        digest = hashlib.sha256(raw.encode()).hexdigest()
        return f"eka:query:{digest}"

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.warning("Cache get failed: %s", e)
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int | None = None) -> None:
        try:
            client = await self._get_client()
            ttl = ttl or settings.CACHE_TTL_SECONDS
            await client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.warning("Cache set failed: %s", e)

    async def delete(self, key: str) -> None:
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception as e:
            logger.warning("Cache delete failed: %s", e)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None