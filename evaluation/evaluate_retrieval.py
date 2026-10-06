"""
Retrieval evaluation script.
Measures whether the retriever returns relevant chunks for a set of questions
while respecting access control.
"""
import asyncio
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import User
from app.retrieval.retriever import Retriever
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


async def evaluate_retrieval(session: AsyncSession, user: User, dataset: list) -> dict:
    retriever = Retriever(session)
    results = []

    for item in dataset:
        contexts = await retriever.retrieve(item["question"], user)
        content = " ".join(c.get("content", "") for c in contexts).lower()

        keyword_hits = sum(1 for kw in item.get("expected_keywords", []) if kw.lower() in content)
        total_keywords = len(item.get("expected_keywords", [])) or 1
        relevance = keyword_hits / total_keywords

        results.append({
            "id": item["id"],
            "question": item["question"],
            "retrieved_count": len(contexts),
            "keyword_hits": keyword_hits,
            "relevance": round(relevance, 3),
            "access_levels_returned": list({c.get("access_level") for c in contexts}),
        })

    avg_relevance = sum(r["relevance"] for r in results) / max(len(results), 1)
    return {
        "average_relevance": round(avg_relevance, 3),
        "details": results,
    }


async def main():
    await init_db()
    dataset_path = Path("evaluation/dataset.json")
    dataset = json.loads(dataset_path.read_text())

    async with AsyncSessionLocal() as session:
        # Use a synthetic ENGINEER user for evaluation
        user = User(email="eval@example.com", password_hash="x", role="ENGINEER")
        report = await evaluate_retrieval(session, user, dataset)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())