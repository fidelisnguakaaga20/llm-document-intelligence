import os
from typing import Tuple
from pypdf import PdfReader


ALLOWED_EXTENSIONS = {".pdf", ".txt"}


def extract_text_from_txt(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()

    # Safe decode
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="ignore")


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    parts = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        parts.append(txt)

    text = "\n".join(parts).strip()
    return text


def extract_text(file_path: str) -> Tuple[bool, str]:
    """
    Returns (success, text_or_error)
    """
    if not os.path.exists(file_path):
        return False, f"File not found on disk: {file_path}"

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type for extraction: {ext}"

    try:
        if ext == ".txt":
            text = extract_text_from_txt(file_path)
        else:
            text = extract_text_from_pdf(file_path)

        if not text.strip():
            return False, "No text could be extracted (empty result)"

        return True, text

    except Exception as e:
        return False, f"Extraction error: {str(e)}"