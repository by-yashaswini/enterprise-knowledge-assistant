from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_active_user
from app.db.database import get_async_session
from app.db.models import User
from app.schemas.documents import DocumentListResponse, DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    title: Annotated[Optional[str], Form()] = None,
    document_type: Annotated[str, Form()] = "general",
    access_level: Annotated[str, Form()] = "INTERNAL",
) -> DocumentUploadResponse:
    service = DocumentService(session)
    doc = await service.upload_document(
        file=file,
        owner=current_user,
        title=title,
        document_type=document_type,
        access_level=access_level,
    )
    # Count chunks
    chunk_count = len(doc.chunks) if doc.chunks else 0
    return DocumentUploadResponse(
        id=doc.id,
        title=doc.title,
        filename=doc.filename,
        document_type=doc.document_type,
        access_level=doc.access_level,
        chunk_count=chunk_count,
        created_at=doc.created_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = 0,
    limit: int = 50,
) -> DocumentListResponse:
    service = DocumentService(session)
    documents, total = await service.list_documents(current_user, skip=skip, limit=limit)
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> DocumentResponse:
    service = DocumentService(session)
    doc = await service.get_document(document_id, current_user)
    return DocumentResponse.model_validate(doc)