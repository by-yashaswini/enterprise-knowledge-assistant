from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_active_user
from app.db.database import get_async_session
from app.db.models import User
from app.schemas.query import QueryRequest, QueryResponse, SourceCitation
from app.services.query_service import QueryService

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> QueryResponse:
    service = QueryService(session)
    result = await service.answer(body.question, current_user)

    sources = [SourceCitation(**s) for s in result.get("sources", [])]
    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        context_used=result.get("context_used", 0),
        cached=result.get("cached", False),
    )