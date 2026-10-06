from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import User
from app.rag.chain import RAGChain
from app.retrieval.retriever import Retriever
from app.services.cache_service import CacheService

logger = get_logger(__name__)


class QueryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.retriever = Retriever(session)
        self.rag = RAGChain()
        self.cache = CacheService()

    async def answer(self, question: str, user: User) -> dict[str, Any]:
        # Authorization-safe cache key
        cache_key = self.cache.make_key(question, user.role, user.id)

        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for user %s", user.email)
            cached["cached"] = True
            return cached

        contexts = await self.retriever.retrieve(question, user)
        result = await self.rag.generate(question, contexts)
        result["cached"] = False

        # Store in cache
        await self.cache.set(cache_key, result)

        return result