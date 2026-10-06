import uuid
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import Document, DocumentChunk, User
from app.ingestion.chunker import chunk_text
from app.ingestion.cleaner import clean_text
from app.ingestion.embeddings import get_embedding_service
from app.ingestion.loader import load_document

logger = get_logger(__name__)
settings = get_settings()


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.embedding_service = get_embedding_service()

    async def upload_document(
        self,
        file: UploadFile,
        owner: User,
        title: Optional[str] = None,
        document_type: str = "general",
        access_level: str = "INTERNAL",
    ) -> Document:
        # Validate extension
        filename = file.filename or "unknown"
        suffix = Path(filename).suffix.lower()
        if suffix not in settings.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {settings.SUPPORTED_EXTENSIONS}",
            )

        # Validate size
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB} MB",
            )

        # Persist temporarily
        upload_dir = Path("data/documents")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / f"{uuid.uuid4()}{suffix}"
        temp_path.write_bytes(content)

        try:
            raw_text, meta = load_document(temp_path)
            cleaned = clean_text(raw_text)
            chunks = chunk_text(cleaned)

            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No usable text could be extracted from the document",
                )

            embeddings = await self.embedding_service.embed_documents(chunks)

            doc = Document(
                title=title or Path(filename).stem,
                filename=filename,
                document_type=document_type,
                access_level=access_level.upper(),
                owner_id=owner.id,
                metadata_={
                    "page_count": meta.get("page_count"),
                    "original_filename": filename,
                    "char_count": len(cleaned),
                },
            )
            self.session.add(doc)
            await self.session.flush()

            for idx, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk_content,
                    embedding=embedding,
                    metadata_={"chunk_index": idx},
                )
                self.session.add(chunk)

            await self.session.flush()
            await self.session.refresh(doc)
            logger.info(
                "Document ingested: id=%s title=%s chunks=%d access=%s",
                doc.id,
                doc.title,
                len(chunks),
                doc.access_level,
            )
            return doc
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    async def list_documents(
        self,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Document], int]:
        # Simple visibility: user sees documents they are allowed to access
        from app.retrieval.access_control import get_allowed_access_levels

        allowed = get_allowed_access_levels(user.role)
        stmt = (
            select(Document)
            .where(Document.access_level.in_(allowed))
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        documents = list(result.scalars().all())

        count_stmt = select(Document).where(Document.access_level.in_(allowed))
        total_result = await self.session.execute(count_stmt)
        total = len(total_result.scalars().all())
        return documents, total

    async def get_document(self, document_id: UUID, user: User) -> Document:
        from app.retrieval.access_control import get_allowed_access_levels

        allowed = get_allowed_access_levels(user.role)
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.chunks))
        )
        result = await self.session.execute(stmt)
        doc = result.scalar_one_or_none()

        if doc is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        if doc.access_level not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this document",
            )
        return doc