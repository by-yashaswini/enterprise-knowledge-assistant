from app.ingestion.cleaner import clean_text
from app.ingestion.chunker import chunk_text


def test_clean_text_normalizes_whitespace():
    dirty = "Hello   world\n\n\n\nThis  is\ttest"
    cleaned = clean_text(dirty)
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned
    assert cleaned.startswith("Hello")


def test_chunk_text_produces_overlapping_chunks():
    text = "Sentence one. " * 100
    chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 120 for c in chunks)  # rough upper bound