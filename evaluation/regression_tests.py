"""
Regression tests for the RAG + access-control pipeline.
These tests are designed to catch silent breaks in security or grounding.
"""
import asyncio
import pytest
from uuid import uuid4

from app.db.database import AsyncSessionLocal, init_db
from app.db.models import User
from app.retrieval.access_control import get_allowed_access_levels
from app.retrieval.retriever import Retriever
from app.services.query_service import QueryService


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_access_control_mapping():
    assert "ADMIN" in get_allowed_access_levels("ADMIN")
    assert "SECURITY" in get_allowed_access_levels("ADMIN")
    assert "SECURITY" not in get_allowed_access_levels("ENGINEER")
    assert "ENGINEERING" not in get_allowed_access_levels("EMPLOYEE")
    assert get_allowed_access_levels("UNKNOWN") == ["PUBLIC"]


@pytest.mark.asyncio
async def test_unauthorized_document_never_returned():
    """
    Critical security regression:
    An ENGINEER must never receive ADMIN-only or SECURITY-only chunks.
    """
    await init_db()
    async with AsyncSessionLocal() as session:
        engineer = User(id=uuid4(), email="eng@test.com", password_hash="x", role="ENGINEER")
        retriever = Retriever(session)
        results = await retriever.retrieve(
            "security incident response procedure",
            engineer,
        )
        for r in results:
            assert r.get("access_level") not in {"ADMIN", "SECURITY"}, (
                f"Unauthorized access level leaked: {r.get('access_level')}"
            )


@pytest.mark.asyncio
async def test_empty_retrieval_produces_refusal():
    await init_db()
    async with AsyncSessionLocal() as session:
        user = User(id=uuid4(), email="emp@test.com", password_hash="x", role="EMPLOYEE")
        service = QueryService(session)
        result = await service.answer(
            "What is the secret launch code of the Mars rover?",
            user,
        )
        answer = result["answer"].lower()
        assert "do not have enough information" in answer or "insufficient" in answer
        assert result.get("context_used", 0) == 0 or len(result.get("sources", [])) == 0