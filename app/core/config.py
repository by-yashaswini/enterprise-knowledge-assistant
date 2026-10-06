from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Enterprise Knowledge Intelligence Assistant"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # FastAPI / Server
    API_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"])

    # Security / JWT
    SECRET_KEY: str = Field(..., min_length=32, description="Must be a strong random string")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (PostgreSQL + pgvector)
    POSTGRES_USER: str = "eka_user"
    POSTGRES_PASSWORD: str = Field(..., min_length=8)
    POSTGRES_DB: str = "enterprise_knowledge"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # LLM
    LLM_PROVIDER: str = Field(default="openai", description="openai | other")
    LLM_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: Optional[str] = None
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024

    # Embeddings
    EMBEDDING_PROVIDER: str = Field(default="openai", description="openai | other")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # Ingestion / Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_SIZE_MB: int = 20
    SUPPORTED_EXTENSIONS: List[str] = Field(default_factory=lambda: [".pdf", ".txt"])

    # Retrieval
    RETRIEVAL_TOP_K: int = 8
    RERANK_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.25

    # Access control roles (kept here for reference; enforced in retrieval layer)
    VALID_ROLES: List[str] = Field(default_factory=lambda: ["ADMIN", "ENGINEER", "EMPLOYEE"])
    VALID_ACCESS_LEVELS: List[str] = Field(
        default_factory=lambda: ["PUBLIC", "INTERNAL", "ENGINEERING", "SECURITY", "ADMIN"]
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()