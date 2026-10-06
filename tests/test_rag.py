from app.rag.prompts import build_rag_prompt
from app.rag.citations import build_citations


def test_prompt_contains_context_and_question():
    contexts = [{"document_title": "Policy", "content": "Passwords expire every 90 days."}]
    prompt = build_rag_prompt("How often must passwords be changed?", contexts)
    assert "90 days" in prompt
    assert "How often must passwords be changed?" in prompt
    assert "ONLY the provided context" in prompt


def test_build_citations_deduplicates():
    contexts = [
        {"document_id": "d1", "document_title": "Policy A", "similarity": 0.9},
        {"document_id": "d1", "document_title": "Policy A", "similarity": 0.8},
        {"document_id": "d2", "document_title": "Policy B", "similarity": 0.7},
    ]
    citations = build_citations(contexts)
    assert len(citations) == 2