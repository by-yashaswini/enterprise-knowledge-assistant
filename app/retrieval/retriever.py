from typing import Any, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import User
from app.db.vector_store import similarity_search
from app.ingestion.embeddings import get_embedding_service
from app.retrieval.access_control import get_allowed_access_levels
from app.retrieval.reranker import simple_rerank

logger = get_logger(__name__)
settings = get_settings()


class Retriever:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.embedding_service = get_embedding_service()

    async def retrieve(
        self,
        query: str,
        user: User,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        use_reranker: bool = True,
    ) -> List[dict[str, Any]]:
        """
        Perform authorized semantic retrieval.

        Security invariant:
        Only chunks belonging to documents the user is allowed to access
        are ever returned. Filtering happens inside the SQL query.
        """
        allowed_levels = get_allowed_access_levels(user.role)
        k = top_k or settings.RETRIEVAL_TOP_K
        threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD

        query_embedding = await self.embedding_service.embed_query(query)

        results = await similarity_search(
            self.session,
            query_embedding,
            allowed_access_levels=allowed_levels,
            top_k=k * 2 if use_reranker else k,  # over-fetch if reranking
            similarity_threshold=threshold,
        )

        if use_reranker and results:
            results = simple_rerank(query, results, top_k=settings.RERANK_TOP_K)

        logger.info(
            "Retrieval for user %s (role=%s): %d chunks returned",
            user.email,
            user.role,
            len(results),
        )
        return results