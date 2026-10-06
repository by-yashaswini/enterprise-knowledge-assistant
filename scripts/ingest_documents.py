"""
Bulk-ingest all PDF/TXT files from data/documents/ using an admin user.

Pipeline:
    Document file
        ↓
    Load text
        ↓
    Clean text
        ↓
    Chunk text
        ↓
    Generate embeddings
        ↓
    Store document + chunks in PostgreSQL/pgvector
        ↓
    Commit transaction
"""

import asyncio
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select

from app.core.logging import get_logger, setup_logging
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import User
from app.services.document_service import DocumentService


setup_logging()
logger = get_logger(__name__)


async def ingest_all() -> None:
    """Ingest all PDF/TXT documents from data/documents/."""

    # Initialize database
    await init_db()

    # Locate documents
    docs_dir = Path("data/documents")
    docs_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        list(docs_dir.glob("*.pdf"))
        + list(docs_dir.glob("*.txt"))
    )

    if not files:
        logger.warning(
            "No PDF/TXT documents found in data/documents/"
        )
        return

    logger.info(
        "Found %d document(s) for ingestion",
        len(files),
    )

    # Open database session
    async with AsyncSessionLocal() as session:

        # Find ADMIN user
        result = await session.execute(
            select(User)
            .where(User.role == "ADMIN")
            .limit(1)
        )

        admin = result.scalar_one_or_none()

        if not admin:
            logger.error(
                "No ADMIN user found. "
                "Run: python -m scripts.seed_database"
            )
            return

        logger.info(
            "Using admin user: %s",
            admin.email,
        )

        # Create document service
        service = DocumentService(session)

        successful = 0
        failed = 0

        # Process every document
        for path in files:

            logger.info(
                "Starting ingestion: %s",
                path.name,
            )

            try:
                # Read file
                content = path.read_bytes()

                # Create UploadFile
                upload = UploadFile(
                    filename=path.name,
                    file=BytesIO(content),
                )

                # Process and store document
                doc = await service.upload_document(
                    file=upload,
                    owner=admin,
                    title=path.stem,
                    access_level="INTERNAL",
                )

                # IMPORTANT:
                # upload_document() uses flush(), so we must
                # explicitly commit the transaction here.
                await session.commit()

                successful += 1

                logger.info(
                    "Successfully ingested: %s | id=%s",
                    path.name,
                    doc.id,
                )

            except Exception as exc:

                # Roll back failed document
                await session.rollback()

                failed += 1

                logger.exception(
                    "Failed to ingest %s: %s",
                    path.name,
                    exc,
                )

        # Final summary
        logger.info(
            "Ingestion complete | successful=%d | failed=%d | total=%d",
            successful,
            failed,
            len(files),
        )


if __name__ == "__main__":
    asyncio.run(ingest_all())