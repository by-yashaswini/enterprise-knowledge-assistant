from typing import Any, List


def build_citations(contexts: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """
    Build a clean list of citation objects from retrieved chunks.
    """
    citations = []
    seen = set()
    for i, ctx in enumerate(contexts, start=1):
        doc_id = str(ctx.get("document_id") or "")
        title = ctx.get("document_title") or "Unknown"
        key = (doc_id, title)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "index": i,
                "document_id": doc_id,
                "title": title,
                "filename": ctx.get("filename"),
                "access_level": ctx.get("access_level"),
                "chunk_index": ctx.get("chunk_index"),
                "similarity": round(float(ctx.get("similarity") or 0.0), 4),
            }
        )
    return citations