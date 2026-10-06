from pathlib import Path
from typing import Tuple

from pypdf import PdfReader

from app.core.logging import get_logger

logger = get_logger(__name__)


def load_document(file_path: str | Path) -> Tuple[str, dict]:
    """
    Load text from a PDF or TXT file.
    Returns (raw_text, metadata).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    metadata = {
        "filename": path.name,
        "source": str(path),
        "extension": suffix,
    }

    if suffix == ".pdf":
        text, extra = _load_pdf(path)
        metadata.update(extra)
    elif suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata["page_count"] = 1
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Only .pdf and .txt are supported.")

    logger.info("Loaded document %s (%d characters)", path.name, len(text))
    return text, metadata


def _load_pdf(path: Path) -> Tuple[str, dict]:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        pages.append(page_text)

    full_text = "\n\n".join(pages)
    extra = {
        "page_count": len(reader.pages),
    }
    return full_text, extra