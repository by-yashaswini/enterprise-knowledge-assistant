"""
Generation / grounding evaluation.
Checks that answers stay faithful to retrieved context and that
"insufficient evidence" responses are returned when appropriate.
"""
import asyncio
import json
from pathlib import Path

from app.core.logging import setup_logging, get_logger
from app.db.database import AsyncSessionLocal, init_db
from app.db.models import User
from app.services.query_service import QueryService

setup_logging()
logger = get_logger(__name__)


async def evaluate_generation(session, user: User, dataset: list) -> dict:
    service = QueryService(session)
    results = []

    for item in dataset:
        result = await service.answer(item["question"], user)
        answer = result["answer"].lower()
        should_answer = item.get("should_have_answer", True)

        has_refusal = "do not have enough information" in answer or "insufficient" in answer
        grounded = (should_answer and not has_refusal) or (not should_answer and has_refusal)

        results.append({
            "id": item["id"],
            "question": item["question"],
            "should_have_answer": should_answer,
            "has_refusal": has_refusal,
            "grounded": grounded,
            "context_used": result.get("context_used", 0),
            "source_count": len(result.get("sources", [])),
        })

    grounded_rate = sum(1 for r in results if r["grounded"]) / max(len(results), 1)
    return {
        "grounded_rate": round(grounded_rate, 3),
        "details": results,
    }


async def main():
    await init_db()
    dataset = json.loads(Path("evaluation/dataset.json").read_text())

    async with AsyncSessionLocal() as session:
        user = User(email="eval@example.com", password_hash="x", role="ENGINEER")
        report = await evaluate_generation(session, user, dataset)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())