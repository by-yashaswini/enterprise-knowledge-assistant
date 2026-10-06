from abc import ABC, abstractmethod
from typing import List

from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService(ABC):
    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        ...


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")

        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions,
        )

        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=[text],
            dimensions=self.dimensions,
        )

        return response.data[0].embedding


class LocalEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        self.model_name = "all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)

        dimensions = self.model.get_embedding_dimension()

        if dimensions != settings.EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Embedding dimension mismatch: model={dimensions}, "
                f"configured={settings.EMBEDDING_DIMENSIONS}"
            )

        logger.info(
            "Loaded local embedding model: %s (%s dimensions)",
            self.model_name,
            dimensions,
        )

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    async def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.tolist()


def get_embedding_service() -> EmbeddingService:
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "openai":
        return OpenAIEmbeddingService()

    if provider == "local":
        return LocalEmbeddingService()

    raise ValueError(f"Unsupported embedding provider: {provider}")
