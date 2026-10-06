from typing import Any, List


def simple_rerank(
    query: str,
    candidates: List[dict[str, Any]],
    top_k: int = 5,
) -> List[dict[str, Any]]:
    """
    Lightweight keyword-aware re-ranking on top of vector similarity.
    Combines vector similarity with simple term overlap.
    """
    if not candidates:
        return []

    query_terms = set(query.lower().split())

    def score(item: dict[str, Any]) -> float:
        content = (item.get("content") or "").lower()
        content_terms = set(content.split())
        overlap = len(query_terms & content_terms) / max(len(query_terms), 1)
        similarity = float(item.get("similarity") or 0.0)
        return 0.7 * similarity + 0.3 * overlap

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[:top_k]