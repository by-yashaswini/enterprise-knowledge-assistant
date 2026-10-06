from typing import Any, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class SourceCitation(BaseModel):
    index: int
    document_id: str
    title: str
    filename: Optional[str] = None
    access_level: Optional[str] = None
    chunk_index: Optional[int] = None
    similarity: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    context_used: int
    cached: bool = False