import re


def clean_text(text: str) -> str:
    """
    Normalize whitespace, remove excessive newlines and non-printable characters.
    """
    if not text:
        return ""

    # Replace non-breaking spaces and other unicode spaces
    text = text.replace("\xa0", " ")

    # Remove control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces / tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Strip leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()