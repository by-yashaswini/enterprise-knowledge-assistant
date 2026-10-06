from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Document, DocumentChunk

logger = get_logger(__name__)
settings = get_settings()


async def ensure_vector_extension(session: AsyncSession) -> None:
    """Create the pgvector extension if it does not exist."""
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await session.commit()
    logger.info("pgvector extension ensured")


async def create_vector_index(session: AsyncSession) -> None:
    """
    Create an HNSW index on the embedding column for fast similarity search.
    Safe to call multiple times (IF NOT EXISTS).
    """
    await session.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
            ON document_chunks
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
            """
        )
    )
    await session.commit()
    logger.info("HNSW vector index ensured")


async def similarity_search(
    session: AsyncSession,
    query_embedding: list[float],
    *,
    allowed_access_levels: Sequence[str],
    top_k: int = 8,
    similarity_threshold: float = 0.25,
) -> list[dict[str, Any]]:
    """
    Perform cosine-similarity search over document chunks,
    filtered by the caller's allowed access levels.

    Returns a list of dicts with chunk data + similarity score.
    """
    if not allowed_access_levels:
        return []

    # Build a safe IN clause
    placeholders = ", ".join(f":level_{i}" for i in range(len(allowed_access_levels)))
    params: dict[str, Any] = {
        f"level_{i}": level for i, level in enumerate(allowed_access_levels)
    }
    params["query_embedding"] = str(query_embedding)
    params["top_k"] = top_k
    params["threshold"] = similarity_threshold

    sql = text(
        f"""
        SELECT
            dc.id              AS chunk_id,
            dc.document_id     AS document_id,
            dc.chunk_index     AS chunk_index,
            dc.content         AS content,
            dc.metadata        AS metadata,
            d.title            AS document_title,
            d.filename         AS filename,
            d.access_level     AS access_level,
            d.document_type    AS document_type,
            1 - (dc.embedding <=> :query_embedding) AS similarity
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.access_level IN ({placeholders})
          AND dc.embedding IS NOT NULL
          AND 1 - (dc.embedding <=> :query_embedding) >= :threshold
        ORDER BY dc.embedding <=> :query_embedding
        LIMIT :top_k
        """
    )

    result = await session.execute(sql, params)
    rows = result.mappings().all()

    return [dict(row) for row in rows]


async def get_chunks_by_document(
    session: AsyncSession,
    document_id: UUID,
) -> list[DocumentChunk]:
    """Return all chunks belonging to a document, ordered by chunk_index."""
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())