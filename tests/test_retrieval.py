from app.retrieval.access_control import get_allowed_access_levels
from app.retrieval.reranker import simple_rerank


def test_role_access_levels():
    assert set(get_allowed_access_levels("ADMIN")) == {
        "PUBLIC", "INTERNAL", "ENGINEERING", "SECURITY", "ADMIN"
    }
    assert "SECURITY" not in get_allowed_access_levels("ENGINEER")
    assert "ENGINEERING" not in get_allowed_access_levels("EMPLOYEE")


def test_simple_reranker_orders_by_score():
    candidates = [
        {"content": "unrelated text", "similarity": 0.9},
        {"content": "password rotation policy every 90 days", "similarity": 0.6},
    ]
    ranked = simple_rerank("password rotation policy", candidates, top_k=2)
    assert "password" in ranked[0]["content"]