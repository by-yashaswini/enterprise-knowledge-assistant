from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DocumentUploadResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    document_type: str
    access_level: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    document_type: str
    access_level: str
    owner_id: UUID
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    document_type: str = Field(default="general", max_length=50)
    access_level: str = Field(default="INTERNAL")

    @field_validator("access_level")
    @classmethod
    def validate_access_level(cls, v: str) -> str:
        allowed = {"PUBLIC", "INTERNAL", "ENGINEERING", "SECURITY", "ADMIN"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"access_level must be one of {allowed}")
        return 